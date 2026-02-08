from fastapi import APIRouter, HTTPException
import paramiko
from sqlmodel import Session, select

from core.config import settings
from db import get_session
from models.host import Host
from schemas.host import HostConnectionTest, HostResponse
from services.ssh_discovery import sync_known_hosts_to_db


router = APIRouter(tags=["hosts"])


@router.get("/hosts", response_model=list[HostResponse])
def list_hosts():
    session: Session = get_session()
    with session:
        return list(session.exec(select(Host)))


@router.get("/hosts/{host_id}", response_model=HostResponse)
def get_host(host_id: int):
    session: Session = get_session()
    with session:
        host = session.get(Host, host_id)
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")
        return host


@router.post("/hosts/refresh")
def refresh_hosts():
    """Re-scan ~/.ssh/config and import any new hosts."""
    discovered, created = sync_known_hosts_to_db()
    return {"discovered": discovered, "created": created}


@router.post("/hosts/test-connection")
def test_connection(payload: HostConnectionTest):
    hostname = payload.hostname
    ssh_user = payload.ssh_user or settings.ssh_user
    port = payload.port

    # Look up host-specific key from database
    session: Session = get_session()
    key_path = settings.ssh_key_path
    with session:
        host = session.exec(
            select(Host).where(Host.hostname == hostname)
        ).first()
        if host and host.identity_file:
            key_path = host.identity_file

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=hostname,
            username=ssh_user,
            key_filename=key_path,
            port=port,
            timeout=10,
        )
        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        client.close()
