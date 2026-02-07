import asyncio
from pathlib import Path

from services import cac_fetch


def test_cac_fetch_offline_cache(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(cac_fetch, "CAC_CACHE_DIR", tmp_path)

    def fake_ensure_repo():
        repo_path = tmp_path / "content"
        repo_path.mkdir(parents=True, exist_ok=True)
        (repo_path / "xccdf" / "rhel").mkdir(parents=True, exist_ok=True)
        (repo_path / "ansible" / "rhel").mkdir(parents=True, exist_ok=True)
        (repo_path / "xccdf" / "rhel" / "xccdf-rhel.xml").write_text("<xml/>")
        (repo_path / "ansible" / "rhel" / "playbook-rhel.yml").write_text("---")
        return repo_path

    monkeypatch.setattr(cac_fetch, "_ensure_repo", fake_ensure_repo)

    repo_path, artifacts = asyncio.run(
        cac_fetch.ensure_cac_cache("rhel", offline=True)
    )
    assert repo_path.exists()
    assert any(item.artifact_type == "xccdf" for item in artifacts)
    assert any(item.artifact_type == "ansible" for item in artifacts)
