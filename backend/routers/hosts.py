from fastapi import APIRouter, HTTPException
import paramiko
from sqlmodel import Session, select

from core.config import settings
from db import get_session
from models.host import Host
from schemas.host import HostConnectionTest, HostCreate, HostResponse, HostUpdate


router = APIRouter(tags=["hosts"])


@router.get("/hosts", response_model=list[HostResponse])
def list_hosts():
    session: Session = get_session()
    with session:
        return list(session.exec(select(Host)))


@router.post("/hosts", response_model=HostResponse)
def create_host(payload: HostCreate):
    session: Session = get_session()
    with session:
        host = Host(
            hostname=payload.hostname,
            ip_address=payload.ip_address,
            ssh_user=payload.ssh_user,
            os_distro=payload.os_distro,
            os_version=payload.os_version,
        )
        session.add(host)
        session.commit()
        session.refresh(host)
        return host


@router.get("/hosts/{host_id}", response_model=HostResponse)
def get_host(host_id: int):
    session: Session = get_session()
    with session:
        host = session.get(Host, host_id)
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")
        return host


@router.put("/hosts/{host_id}", response_model=HostResponse)
def update_host(host_id: int, payload: HostUpdate):
    session: Session = get_session()
    with session:
        host = session.get(Host, host_id)
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(host, key, value)
        session.add(host)
        session.commit()
        session.refresh(host)
        return host


@router.delete("/hosts/{host_id}")
def delete_host(host_id: int):
    session: Session = get_session()
    with session:
        host = session.get(Host, host_id)
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")
        session.delete(host)
        session.commit()
        return {"status": "deleted"}


@router.post("/hosts/test-connection")
def test_connection(payload: HostConnectionTest):
    hostname = payload.hostname
    ssh_user = payload.ssh_user or settings.ssh_user
    port = payload.port

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=hostname,
            username=ssh_user,
            key_filename=settings.ssh_key_path,
            port=port,
            timeout=10,
        )
        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        client.close()
