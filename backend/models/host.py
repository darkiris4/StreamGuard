from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Host(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    alias: str = ""            # Host directive (short name)
    hostname: str              # HostName (resolved address)
    ssh_user: str = "root"     # User
    port: int = 22             # Port
    identity_file: str = ""    # IdentityFile
    proxy_jump: str = ""       # ProxyJump
    # Legacy / extra fields (kept for migration compat)
    ip_address: str = ""
    os_distro: str = ""
    os_version: str = ""
    ssh_key_path: str = ""
    source: str = "ssh_config"
    created_at: datetime = Field(default_factory=datetime.utcnow)
