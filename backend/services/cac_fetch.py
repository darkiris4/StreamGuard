"""CAC content fetch service — online (GitHub releases) and offline (git clone) modes."""

import io
import json
import logging
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from lxml import etree

from core.config import settings
from schemas.cac import CACArtifact, CACProfileInfo

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_PRODUCTS = {
    "rhel7",
    "rhel8",
    "rhel9",
    "fedora",
    "ubuntu2004",
    "ubuntu2204",
    "ubuntu2404",
    "debian11",
    "debian12",
}

DISTRO_FAMILY_MAP: Dict[str, List[str]] = {
    "rhel": ["rhel7", "rhel8", "rhel9"],
    "fedora": ["fedora"],
    "ubuntu": ["ubuntu2004", "ubuntu2204", "ubuntu2404"],
    "debian": ["debian11", "debian12"],
}

CAC_CACHE_DIR = Path(__file__).resolve().parents[1] / "cac_cache"
RELEASES_DIR = CAC_CACHE_DIR / "releases"
REPO_DIR = CAC_CACHE_DIR / "repo"
METADATA_PATH = CAC_CACHE_DIR / "metadata.json"

GITHUB_API_RELEASES = (
    "https://api.github.com/repos/ComplianceAsCode/content/releases/latest"
)
GITHUB_RELEASE_DOWNLOAD = (
    "https://github.com/ComplianceAsCode/content/releases/download/"
    "v{version}/scap-security-guide-{version}.zip"
)
GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/ComplianceAsCode/content/master"
)

_REQUEST_TIMEOUT = 60

# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------


def _read_metadata() -> dict:
    """Read the metadata.json cache descriptor."""
    if METADATA_PATH.exists():
        try:
            return json.loads(METADATA_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _write_metadata(data: dict) -> None:
    """Persist metadata.json."""
    CAC_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_PATH.write_text(json.dumps(data, indent=2))


def _products_for_distro(distro: str) -> List[str]:
    """Resolve a distro argument to a list of product identifiers."""
    if distro in SUPPORTED_PRODUCTS:
        return [distro]
    if distro in DISTRO_FAMILY_MAP:
        return DISTRO_FAMILY_MAP[distro]
    raise ValueError(
        f"Unsupported distro: {distro}. "
        f"Supported: {sorted(SUPPORTED_PRODUCTS | set(DISTRO_FAMILY_MAP.keys()))}"
    )


# ---------------------------------------------------------------------------
# ONLINE mode — GitHub releases
# ---------------------------------------------------------------------------


def _get_latest_release_version() -> str:
    """Query GitHub Releases API for the latest tag."""
    configured = settings.cac_release_version
    if configured and configured != "latest":
        return configured

    resp = requests.get(
        GITHUB_API_RELEASES,
        headers={"Accept": "application/vnd.github+json"},
        timeout=_REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    tag: str = resp.json().get("tag_name", "")
    return tag.lstrip("v")


def _download_release_zip(version: str) -> Path:
    """Download the release ZIP and extract it. Return the extract directory."""
    extract_dir = RELEASES_DIR / version
    if extract_dir.exists() and any(extract_dir.iterdir()):
        logger.info("Release %s already cached at %s", version, extract_dir)
        return extract_dir

    url = GITHUB_RELEASE_DOWNLOAD.format(version=version)
    logger.info("Downloading CAC release ZIP from %s", url)
    resp = requests.get(url, timeout=300, stream=True)
    resp.raise_for_status()

    extract_dir.mkdir(parents=True, exist_ok=True)
    zip_bytes = io.BytesIO(resp.content)
    with zipfile.ZipFile(zip_bytes) as zf:
        for member in zf.namelist():
            # Flatten the top-level directory (e.g. scap-security-guide-0.1.73/)
            parts = member.split("/", 1)
            if len(parts) < 2 or not parts[1]:
                continue
            target = extract_dir / parts[1]
            if member.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(member))

    return extract_dir


def _collect_release_artifacts(
    extract_dir: Path, products: List[str]
) -> List[CACArtifact]:
    """Scan extracted release directory for datastream XMLs and playbooks."""
    artifacts: List[CACArtifact] = []
    for product in products:
        # DataStream XML: ssg-{product}-ds.xml
        ds_path = extract_dir / f"ssg-{product}-ds.xml"
        if ds_path.exists():
            artifacts.append(
                CACArtifact(
                    path=str(ds_path),
                    artifact_type="datastream",
                    product=product,
                )
            )
        # Ansible playbooks: {product}-playbook-{profile}.yml
        for pb in sorted(extract_dir.glob(f"{product}-playbook-*.yml")):
            profile_match = re.match(
                rf"^{re.escape(product)}-playbook-(.+)\.yml$", pb.name
            )
            profile = profile_match.group(1) if profile_match else ""
            artifacts.append(
                CACArtifact(
                    path=str(pb),
                    artifact_type="playbook",
                    product=product,
                    profile=profile,
                )
            )
    return artifacts


def _update_metadata_from_artifacts(
    artifacts: List[CACArtifact], version: str, mode: str
) -> None:
    """Merge new artifact information into metadata.json."""
    meta = _read_metadata()
    meta["version"] = version
    meta["fetched_at"] = datetime.now(timezone.utc).isoformat()
    meta["mode"] = mode
    distros_meta: dict = meta.setdefault("distros", {})
    for art in artifacts:
        prod_meta = distros_meta.setdefault(
            art.product, {"datastream": "", "playbooks": {}}
        )
        if art.artifact_type in ("datastream", "xccdf"):
            prod_meta["datastream"] = art.path
        elif art.artifact_type in ("playbook", "ansible") and art.profile:
            prod_meta["playbooks"][art.profile] = art.path
    _write_metadata(meta)


def _fetch_online(distro: str) -> Tuple[str, List[CACArtifact]]:
    """Online fetch: get latest release, download ZIP, extract, return artifacts."""
    products = _products_for_distro(distro)
    version = _get_latest_release_version()
    extract_dir = _download_release_zip(version)
    artifacts = _collect_release_artifacts(extract_dir, products)
    _update_metadata_from_artifacts(artifacts, version, "online")
    return version, artifacts


# ---------------------------------------------------------------------------
# Raw single-file fetch (for specific profile XML, etc.)
# ---------------------------------------------------------------------------


def fetch_raw_profile(product: str, profile: str = "stig") -> str:
    """Download a single profile definition from the raw GitHub URL."""
    url = f"{GITHUB_RAW_BASE}/products/{product}/profiles/{profile}.profile"
    resp = requests.get(url, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def fetch_raw_file(url: str) -> str:
    """Generic raw file fetch."""
    resp = requests.get(url, timeout=_REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


# ---------------------------------------------------------------------------
# OFFLINE mode — GitPython clone / pull
# ---------------------------------------------------------------------------


def _ensure_repo() -> Path:
    """Clone or pull the ComplianceAsCode repo for offline use."""
    from git import Repo  # lazy import — only needed in offline mode

    REPO_DIR.parent.mkdir(parents=True, exist_ok=True)
    if not REPO_DIR.exists():
        logger.info("Cloning CAC repo to %s", REPO_DIR)
        Repo.clone_from(settings.cac_github_url, str(REPO_DIR))
    else:
        logger.info("Pulling latest changes in %s", REPO_DIR)
        repo = Repo(str(REPO_DIR))
        repo.remotes.origin.pull()
    return REPO_DIR


def _find_repo_datastreams(repo_path: Path, product: str) -> List[CACArtifact]:
    """Find datastream / XCCDF files in a cloned repo for a product."""
    artifacts: List[CACArtifact] = []
    seen: set[str] = set()

    # Check build directory first (pre-built content)
    build_dir = repo_path / "build"
    if build_dir.exists():
        for path in build_dir.rglob(f"ssg-{product}-ds.xml"):
            artifacts.append(
                CACArtifact(
                    path=str(path), artifact_type="datastream", product=product
                )
            )
            seen.add(str(path))

    # Also search for XCCDF content across the repo
    for path in repo_path.rglob("*.xml"):
        lower = path.name.lower()
        if ("xccdf" in lower or f"ssg-{product}-ds" in lower) and product in lower:
            if str(path) not in seen:
                artifacts.append(
                    CACArtifact(
                        path=str(path), artifact_type="xccdf", product=product
                    )
                )
                seen.add(str(path))
    return artifacts


def _find_repo_playbooks(repo_path: Path, product: str) -> List[CACArtifact]:
    """Find Ansible playbooks in a cloned repo for a product."""
    artifacts: List[CACArtifact] = []
    seen: set[str] = set()

    for path in sorted(repo_path.rglob("*.yml")):
        if product not in path.name.lower():
            continue
        if "playbook" in path.name.lower():
            profile_match = re.match(
                rf"^{re.escape(product)}-playbook-(.+)\.yml$", path.name
            )
            profile = profile_match.group(1) if profile_match else ""
            artifacts.append(
                CACArtifact(
                    path=str(path),
                    artifact_type="playbook",
                    product=product,
                    profile=profile,
                )
            )
            seen.add(str(path))

    # Also check ansible/ directory
    ansible_dir = repo_path / "ansible"
    if ansible_dir.exists():
        for path in sorted(ansible_dir.rglob("*.yml")):
            if product in path.name.lower() and str(path) not in seen:
                artifacts.append(
                    CACArtifact(
                        path=str(path),
                        artifact_type="ansible",
                        product=product,
                    )
                )
                seen.add(str(path))
    return artifacts


def _fetch_offline(distro: str) -> Tuple[str, List[CACArtifact]]:
    """Offline fetch: clone/pull repo, find artifacts."""
    products = _products_for_distro(distro)
    repo_path = _ensure_repo()
    artifacts: List[CACArtifact] = []
    for product in products:
        artifacts.extend(_find_repo_datastreams(repo_path, product))
        artifacts.extend(_find_repo_playbooks(repo_path, product))
    _update_metadata_from_artifacts(artifacts, "local", "offline")
    return "local", artifacts


# ---------------------------------------------------------------------------
# Cache fallback
# ---------------------------------------------------------------------------


def _fallback_from_cache(products: List[str]) -> Tuple[str, List[CACArtifact]]:
    """Return whatever we have cached when the live fetch fails."""
    meta = _read_metadata()
    version = meta.get("version", "unknown")
    artifacts: List[CACArtifact] = []

    # Try release cache first
    if version and version not in ("unknown", "local"):
        extract_dir = RELEASES_DIR / version
        if extract_dir.exists():
            artifacts = _collect_release_artifacts(extract_dir, products)
            if artifacts:
                return version, artifacts

    # Try repo cache
    if REPO_DIR.exists():
        for product in products:
            artifacts.extend(_find_repo_datastreams(REPO_DIR, product))
            artifacts.extend(_find_repo_playbooks(REPO_DIR, product))
        if artifacts:
            return "local", artifacts

    return version, []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def ensure_cac_content(
    distro: str, offline: Optional[bool] = None
) -> Tuple[str, List[CACArtifact]]:
    """
    Ensure CAC content is available for the given distro.

    - Online mode (default): download from GitHub releases.
    - Offline mode: clone/pull the full repo.

    Falls back to cached content on network errors.
    """
    use_offline = offline if offline is not None else settings.offline_mode
    products = _products_for_distro(distro)

    try:
        if use_offline:
            return _fetch_offline(distro)
        else:
            return _fetch_online(distro)
    except (requests.RequestException, OSError) as exc:
        logger.warning("Fetch failed (%s), attempting cache fallback", exc)
        return _fallback_from_cache(products)


async def ensure_cac_cache(
    distro: str, offline: bool
) -> Tuple[Path, List[CACArtifact]]:
    """Backward-compatible wrapper used by legacy endpoints."""
    version, artifacts = await ensure_cac_content(distro, offline=offline)
    if offline:
        return REPO_DIR, artifacts
    base = RELEASES_DIR / version if version and version != "unknown" else CAC_CACHE_DIR
    return base, artifacts


def get_cache_status() -> dict:
    """Return current cache status from metadata.json."""
    meta = _read_metadata()
    result = {
        "mode": "offline" if settings.offline_mode else "online",
        "cache_version": meta.get("version", ""),
        "fetched_at": meta.get("fetched_at", ""),
        "available_distros": sorted(meta.get("distros", {}).keys()),
        "profiles": {},
    }
    for prod, prod_meta in meta.get("distros", {}).items():
        result["profiles"][prod] = sorted(prod_meta.get("playbooks", {}).keys())
    return result


def parse_profiles_from_datastream(distro: str) -> List[CACProfileInfo]:
    """Parse XCCDF/datastream XML to extract Profile ids and titles."""
    meta = _read_metadata()
    products = _products_for_distro(distro)
    profiles: List[CACProfileInfo] = []

    for product in products:
        prod_meta = meta.get("distros", {}).get(product, {})
        ds_path = prod_meta.get("datastream", "")
        if not ds_path or not Path(ds_path).exists():
            continue
        try:
            tree = etree.parse(ds_path)
            for profile_el in tree.iter("{*}Profile"):
                pid = profile_el.get("id", "")
                title_el = profile_el.find("{*}title")
                title = (
                    title_el.text
                    if title_el is not None and title_el.text
                    else pid
                )
                profiles.append(CACProfileInfo(id=pid, title=title))
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.warning("Failed to parse datastream %s: %s", ds_path, exc)

    return profiles


def resolve_content_paths(distro: str, profile_name: str) -> Tuple[str, str]:
    """
    Resolve datastream path and playbook path from cached metadata.

    Returns ``(datastream_path, playbook_path)``.  Either may be empty string
    if not available.
    """
    meta = _read_metadata()
    products = _products_for_distro(distro)

    ds_path = ""
    pb_path = ""
    for product in products:
        prod_meta = meta.get("distros", {}).get(product, {})
        if not ds_path and prod_meta.get("datastream"):
            candidate = prod_meta["datastream"]
            if Path(candidate).exists():
                ds_path = candidate
        if not pb_path:
            candidate = prod_meta.get("playbooks", {}).get(profile_name, "")
            if candidate and Path(candidate).exists():
                pb_path = candidate
    return ds_path, pb_path
