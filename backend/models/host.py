from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Host(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hostname: str
    ip_address: str = ""
    ssh_user: str = "root"
    os_distro: str = ""
    os_version: str = ""
    ssh_key_path: str = ""  # per-host key override; empty = use global default
    source: str = "manual"  # "manual" | "known_hosts"
    created_at: datetime = Field(default_factory=datetime.utcnow)
