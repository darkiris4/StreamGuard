from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HostCreate(BaseModel):
    hostname: str
    ip_address: str = ""
    ssh_user: str = "root"
    os_distro: str = ""
    os_version: str = ""
    ssh_key_path: str = ""


class HostUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    ssh_user: Optional[str] = None
    os_distro: Optional[str] = None
    os_version: Optional[str] = None
    ssh_key_path: Optional[str] = None


class HostResponse(BaseModel):
    id: int
    hostname: str
    ip_address: str
    ssh_user: str
    os_distro: str
    os_version: str
    ssh_key_path: str
    source: str
    created_at: datetime


class HostConnectionTest(BaseModel):
    hostname: str
    ssh_user: str | None = None
    port: int = 22
