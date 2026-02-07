from typing import List

from pydantic import BaseModel


class MitigateRequest(BaseModel):
    hosts: List[str]
    distro: str
    profile_name: str
    playbook_path: str
    dry_run: bool = True


class MitigateResponse(BaseModel):
    job_id: int
    status: str
