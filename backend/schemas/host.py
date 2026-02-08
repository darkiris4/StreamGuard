from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HostResponse(BaseModel):
    id: int
    alias: str
    hostname: str
    ssh_user: str
    port: int
    identity_file: str
    proxy_jump: str
    created_at: datetime


class HostConnectionTest(BaseModel):
    hostname: str
    ssh_user: str | None = None
    port: int = 22
