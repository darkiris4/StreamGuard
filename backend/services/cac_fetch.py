from pathlib import Path
from typing import Iterable

import requests
from git import Repo

from core.config import settings
from schemas.cac import CACArtifact


SUPPORTED_DISTROS = {"rhel", "ubuntu", "debian"}
CAC_CACHE_DIR = Path(__file__).resolve().parents[1] / "cac_cache"
DEFAULT_REPO_NAME = "content"


def _repo_path() -> Path:
    return CAC_CACHE_DIR / DEFAULT_REPO_NAME


def _ensure_repo() -> Path:
    repo_path = _repo_path()
    repo_path.parent.mkdir(parents=True, exist_ok=True)
    if not repo_path.exists():
        Repo.clone_from(settings.cac_github_url, repo_path)
    else:
        repo = Repo(repo_path)
        repo.remotes.origin.pull()
    return repo_path


def _filter_artifacts(paths: Iterable[Path], artifact_type: str) -> list[CACArtifact]:
    return [
        CACArtifact(path=str(path), artifact_type=artifact_type)
        for path in paths
    ]


def _find_xccdf(repo_path: Path, distro: str) -> list[CACArtifact]:
    candidates = []
    for path in repo_path.rglob("*.xml"):
        lower = str(path).lower()
        if "xccdf" in lower and distro in lower:
            candidates.append(path)
    return _filter_artifacts(candidates, "xccdf")


def _find_ansible(repo_path: Path, distro: str) -> list[CACArtifact]:
    candidates = []
    for path in repo_path.rglob("*.yml"):
        lower = str(path).lower()
        if "ansible" in lower and distro in lower:
            candidates.append(path)
    return _filter_artifacts(candidates, "ansible")


def get_cache_status(distro: str) -> tuple[bool, Path]:
    if distro not in SUPPORTED_DISTROS:
        raise ValueError(f"Unsupported distro: {distro}")
    repo_path = _repo_path()
    return repo_path.exists(), repo_path


async def ensure_cac_cache(distro: str, offline: bool) -> tuple[Path, list[CACArtifact]]:
    if distro not in SUPPORTED_DISTROS:
        raise ValueError(f"Unsupported distro: {distro}")

    if offline:
        repo_path = _ensure_repo()
        artifacts = _find_xccdf(repo_path, distro) + _find_ansible(
            repo_path, distro
        )
        return repo_path, artifacts

    repo_path = _repo_path()
    artifacts = _find_xccdf(repo_path, distro) + _find_ansible(
        repo_path, distro
    )
    if not artifacts:
        return repo_path, []
    return repo_path, artifacts


def fetch_raw_file(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text
