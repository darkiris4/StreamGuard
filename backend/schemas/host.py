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
    ip_address: str
    os_distro: str
    os_version: str
    created_at: datetime


class HostCreate(BaseModel):
    hostname: str
    alias: str = ""
    ssh_user: str = "root"
    port: int = 22
    identity_file: str = ""
    proxy_jump: str = ""
    ip_address: str = ""
    os_distro: str = ""
    os_version: str = ""


class HostUpdate(BaseModel):
    hostname: Optional[str] = None
    alias: Optional[str] = None
    ssh_user: Optional[str] = None
    port: Optional[int] = None
    identity_file: Optional[str] = None
    proxy_jump: Optional[str] = None
    ip_address: Optional[str] = None
    os_distro: Optional[str] = None
    os_version: Optional[str] = None


class HostConnectionTest(BaseModel):
    hostname: str
    ssh_user: str | None = None
    port: int = 22
