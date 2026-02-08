from typing import Dict, List

from pydantic import BaseModel


class CACArtifact(BaseModel):
    path: str
    artifact_type: str  # "datastream", "playbook", "xccdf", "ansible"
    product: str = ""
    profile: str = ""


class CACFetchResponse(BaseModel):
    distro: str
    offline: bool
    repo_path: str
    artifacts: List[CACArtifact]
    version: str = ""
    job_id: str = ""


class CACCacheStatus(BaseModel):
    distro: str
    cache_exists: bool
    repo_path: str


class CACStatusResponse(BaseModel):
    mode: str  # "online" or "offline"
    cache_version: str
    fetched_at: str
    available_distros: List[str]
    profiles: Dict[str, List[str]]  # product -> list of profile names


class CACProfileInfo(BaseModel):
    id: str
    title: str


class CACProfilesResponse(BaseModel):
    distro: str
    profiles: List[CACProfileInfo]
