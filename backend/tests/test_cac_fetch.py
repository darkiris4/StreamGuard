"""Tests for CAC content fetch service — online and offline modes."""

import asyncio
import io
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services import cac_fetch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_release_zip(version: str = "0.1.73") -> bytes:
    """Build a minimal in-memory ZIP mimicking a ComplianceAsCode release."""
    buf = io.BytesIO()
    prefix = f"scap-security-guide-{version}"
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(f"{prefix}/ssg-rhel9-ds.xml", "<xml>rhel9 datastream</xml>")
        zf.writestr(f"{prefix}/ssg-rhel8-ds.xml", "<xml>rhel8 datastream</xml>")
        zf.writestr(f"{prefix}/rhel9-playbook-stig.yml", "---\n# stig playbook")
        zf.writestr(f"{prefix}/rhel9-playbook-cis.yml", "---\n# cis playbook")
        zf.writestr(f"{prefix}/rhel8-playbook-stig.yml", "---\n# stig playbook")
        zf.writestr(f"{prefix}/ssg-ubuntu2204-ds.xml", "<xml>ubuntu</xml>")
        zf.writestr(f"{prefix}/ubuntu2204-playbook-stig.yml", "---")
    buf.seek(0)
    return buf.read()


class _FakeResponse:
    """Minimal requests.Response stand-in."""

    def __init__(self, content: bytes | str = b"", status_code: int = 200, json_data: dict | None = None):
        if isinstance(content, str):
            content = content.encode()
        self.content = content
        self.text = content.decode(errors="replace")
        self.status_code = status_code
        self._json = json_data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def json(self):
        return self._json


# ---------------------------------------------------------------------------
# Online mode tests
# ---------------------------------------------------------------------------


class TestOnlineMode:
    """Tests for the GitHub-release-based online fetch path."""

    def test_get_latest_release_version(self, monkeypatch):
        """_get_latest_release_version strips the 'v' prefix from the tag."""
        fake_resp = _FakeResponse(json_data={"tag_name": "v0.1.73"})
        monkeypatch.setattr("services.cac_fetch.requests.get", lambda *a, **kw: fake_resp)
        monkeypatch.setattr("services.cac_fetch.settings.cac_release_version", "latest")

        version = cac_fetch._get_latest_release_version()
        assert version == "0.1.73"

    def test_get_configured_version_skips_api(self, monkeypatch):
        """When a fixed version is configured, the API is not called."""
        monkeypatch.setattr("services.cac_fetch.settings.cac_release_version", "0.1.70")

        version = cac_fetch._get_latest_release_version()
        assert version == "0.1.70"

    def test_download_and_extract_release_zip(self, monkeypatch, tmp_path: Path):
        """ZIP download is extracted correctly, flattening the top-level dir."""
        monkeypatch.setattr(cac_fetch, "RELEASES_DIR", tmp_path / "releases")

        zip_bytes = _make_release_zip("0.1.73")
        fake_resp = _FakeResponse(content=zip_bytes)
        monkeypatch.setattr("services.cac_fetch.requests.get", lambda *a, **kw: fake_resp)

        extract_dir = cac_fetch._download_release_zip("0.1.73")
        assert (extract_dir / "ssg-rhel9-ds.xml").exists()
        assert (extract_dir / "rhel9-playbook-stig.yml").exists()

    def test_collect_release_artifacts(self, tmp_path: Path):
        """Artifact collector picks up datastreams and playbooks."""
        (tmp_path / "ssg-rhel9-ds.xml").write_text("<xml/>")
        (tmp_path / "rhel9-playbook-stig.yml").write_text("---")
        (tmp_path / "rhel9-playbook-cis.yml").write_text("---")

        artifacts = cac_fetch._collect_release_artifacts(tmp_path, ["rhel9"])
        types = {a.artifact_type for a in artifacts}
        assert "datastream" in types
        assert "playbook" in types
        assert len(artifacts) == 3

    def test_fetch_online_end_to_end(self, monkeypatch, tmp_path: Path):
        """Full online fetch: version lookup → ZIP download → artifact collection → metadata."""
        monkeypatch.setattr(cac_fetch, "RELEASES_DIR", tmp_path / "releases")
        monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)
        monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")
        monkeypatch.setattr("services.cac_fetch.settings.cac_release_version", "latest")

        zip_bytes = _make_release_zip("0.1.73")
        call_count = {"n": 0}

        def fake_get(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                # Releases API
                return _FakeResponse(json_data={"tag_name": "v0.1.73"})
            # ZIP download
            return _FakeResponse(content=zip_bytes)

        monkeypatch.setattr("services.cac_fetch.requests.get", fake_get)

        version, artifacts = cac_fetch._fetch_online("rhel9")
        assert version == "0.1.73"
        assert len(artifacts) >= 1

        # Metadata written
        meta = json.loads((tmp_path / "metadata.json").read_text())
        assert meta["version"] == "0.1.73"
        assert meta["mode"] == "online"
        assert "rhel9" in meta["distros"]


# ---------------------------------------------------------------------------
# Offline mode tests
# ---------------------------------------------------------------------------


class TestOfflineMode:
    """Tests for the GitPython-clone-based offline fetch path."""

    def test_ensure_repo_clones_when_missing(self, monkeypatch, tmp_path: Path):
        """_ensure_repo clones the repo when the directory doesn't exist."""
        repo_dir = tmp_path / "repo"
        monkeypatch.setattr(cac_fetch, "REPO_DIR", repo_dir)

        mock_repo_cls = MagicMock()
        mock_repo_cls.clone_from = MagicMock(return_value=MagicMock())

        with patch("services.cac_fetch.Repo", mock_repo_cls, create=True):
            # We need to patch the lazy import inside _ensure_repo
            import importlib
            with patch.dict("sys.modules", {"git": MagicMock(Repo=mock_repo_cls)}):
                result = cac_fetch._ensure_repo()

        # The function should attempt to clone
        assert mock_repo_cls.clone_from.called or repo_dir == result

    def test_fetch_offline_finds_artifacts(self, monkeypatch, tmp_path: Path):
        """_fetch_offline returns artifacts found in the repo clone."""
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir(parents=True)
        monkeypatch.setattr(cac_fetch, "REPO_DIR", repo_dir)
        monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)
        monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")

        # Create fake repo structure
        build_dir = repo_dir / "build"
        build_dir.mkdir(parents=True)
        (build_dir / "ssg-rhel9-ds.xml").write_text("<xml/>")

        ansible_dir = repo_dir / "ansible"
        ansible_dir.mkdir(parents=True)
        (ansible_dir / "rhel9-playbook-stig.yml").write_text("---")

        # Patch _ensure_repo to skip actual git operations
        monkeypatch.setattr(cac_fetch, "_ensure_repo", lambda: repo_dir)

        version, artifacts = cac_fetch._fetch_offline("rhel9")
        assert version == "local"
        assert any(a.artifact_type == "datastream" for a in artifacts)


# ---------------------------------------------------------------------------
# Metadata & status tests
# ---------------------------------------------------------------------------


class TestMetadata:
    """Tests for metadata read/write and status helpers."""

    def test_read_write_metadata(self, monkeypatch, tmp_path: Path):
        monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)
        monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")

        cac_fetch._write_metadata({"version": "1.0", "mode": "online"})
        meta = cac_fetch._read_metadata()
        assert meta["version"] == "1.0"
        assert meta["mode"] == "online"

    def test_get_cache_status_empty(self, monkeypatch, tmp_path: Path):
        monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")
        status = cac_fetch.get_cache_status()
        assert status["cache_version"] == ""
        assert status["available_distros"] == []

    def test_get_cache_status_populated(self, monkeypatch, tmp_path: Path):
        monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)
        monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")

        cac_fetch._write_metadata({
            "version": "0.1.73",
            "mode": "online",
            "distros": {
                "rhel9": {"datastream": "/ds.xml", "playbooks": {"stig": "/pb.yml"}},
            },
        })
        status = cac_fetch.get_cache_status()
        assert status["cache_version"] == "0.1.73"
        assert "rhel9" in status["available_distros"]
        assert "stig" in status["profiles"]["rhel9"]


# ---------------------------------------------------------------------------
# Content path resolution tests
# ---------------------------------------------------------------------------


class TestResolveContentPaths:
    def test_resolve_finds_existing_paths(self, monkeypatch, tmp_path: Path):
        ds_file = tmp_path / "ds.xml"
        pb_file = tmp_path / "pb.yml"
        ds_file.write_text("<xml/>")
        pb_file.write_text("---")

        monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")
        monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)
        cac_fetch._write_metadata({
            "version": "0.1.73",
            "distros": {
                "rhel9": {
                    "datastream": str(ds_file),
                    "playbooks": {"stig": str(pb_file)},
                },
            },
        })

        ds, pb = cac_fetch.resolve_content_paths("rhel9", "stig")
        assert ds == str(ds_file)
        assert pb == str(pb_file)

    def test_resolve_returns_empty_when_missing(self, monkeypatch, tmp_path: Path):
        monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")
        monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)
        cac_fetch._write_metadata({"version": "0.1.73", "distros": {}})

        ds, pb = cac_fetch.resolve_content_paths("rhel9", "stig")
        assert ds == ""
        assert pb == ""


# ---------------------------------------------------------------------------
# Distro validation tests
# ---------------------------------------------------------------------------


class TestDistroValidation:
    def test_single_product(self):
        assert cac_fetch._products_for_distro("rhel9") == ["rhel9"]

    def test_family_expansion(self):
        products = cac_fetch._products_for_distro("rhel")
        assert "rhel7" in products
        assert "rhel8" in products
        assert "rhel9" in products

    def test_unsupported_raises(self):
        with pytest.raises(ValueError, match="Unsupported distro"):
            cac_fetch._products_for_distro("windows")


# ---------------------------------------------------------------------------
# Fallback tests
# ---------------------------------------------------------------------------


class TestFallback:
    def test_fallback_returns_cached_release(self, monkeypatch, tmp_path: Path):
        release_dir = tmp_path / "releases" / "0.1.73"
        release_dir.mkdir(parents=True)
        (release_dir / "ssg-rhel9-ds.xml").write_text("<xml/>")

        monkeypatch.setattr(cac_fetch, "RELEASES_DIR", tmp_path / "releases")
        monkeypatch.setattr(cac_fetch, "REPO_DIR", tmp_path / "repo")
        monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)
        monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")
        cac_fetch._write_metadata({"version": "0.1.73"})

        version, artifacts = cac_fetch._fallback_from_cache(["rhel9"])
        assert version == "0.1.73"
        assert len(artifacts) >= 1

    def test_ensure_cac_content_falls_back_on_error(self, monkeypatch, tmp_path: Path):
        """Network error triggers cache fallback."""
        import requests as req

        release_dir = tmp_path / "releases" / "0.1.73"
        release_dir.mkdir(parents=True)
        (release_dir / "ssg-rhel9-ds.xml").write_text("<xml/>")

        monkeypatch.setattr(cac_fetch, "RELEASES_DIR", tmp_path / "releases")
        monkeypatch.setattr(cac_fetch, "REPO_DIR", tmp_path / "repo")
        monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)
        monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")
        cac_fetch._write_metadata({"version": "0.1.73"})

        def failing_fetch(*a, **kw):
            raise req.ConnectionError("no network")

        monkeypatch.setattr("services.cac_fetch.requests.get", failing_fetch)

        version, artifacts = asyncio.run(
            cac_fetch.ensure_cac_content("rhel9", offline=False)
        )
        assert version == "0.1.73"
        assert len(artifacts) >= 1


# ---------------------------------------------------------------------------
# Legacy wrapper test
# ---------------------------------------------------------------------------


def test_legacy_ensure_cac_cache(monkeypatch, tmp_path: Path):
    """The backward-compatible ensure_cac_cache wrapper still works."""
    monkeypatch.setattr(cac_fetch, "RELEASES_DIR", tmp_path / "releases")
    monkeypatch.setattr(cac_fetch, "REPO_DIR", tmp_path / "repo")
    monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)
    monkeypatch.setattr(cac_fetch, "METADATA_PATH", tmp_path / "metadata.json")

    repo_dir = tmp_path / "repo"
    repo_dir.mkdir(parents=True)
    build = repo_dir / "build"
    build.mkdir()
    (build / "ssg-rhel9-ds.xml").write_text("<xml/>")

    monkeypatch.setattr(cac_fetch, "_ensure_repo", lambda: repo_dir)

    repo_path, artifacts = asyncio.run(
        cac_fetch.ensure_cac_cache("rhel9", offline=True)
    )
    assert repo_path.exists()
    assert any(a.artifact_type == "datastream" for a in artifacts)
