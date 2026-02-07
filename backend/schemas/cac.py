from typing import List

from pydantic import BaseModel


class CACArtifact(BaseModel):
    path: str
    artifact_type: str


class CACFetchResponse(BaseModel):
    distro: str
    offline: bool
    repo_path: str
    artifacts: List[CACArtifact]


class CACCacheStatus(BaseModel):
    distro: str
    cache_exists: bool
    repo_path: str
