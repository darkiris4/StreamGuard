from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from db import get_session
from models.job import MitigationJob
from schemas.job import JobHistoryItem

from schemas.mitigate import MitigateRequest, MitigateResponse
from services.mitigate import run_mitigation


router = APIRouter(tags=["mitigate"])


@router.post("/mitigate", response_model=MitigateResponse)
async def mitigate_hosts(payload: MitigateRequest):
    if not payload.playbook_path:
        raise HTTPException(
            status_code=400, detail="playbook_path is required for mitigation"
        )
    job_id, status = await run_mitigation(
        payload.hosts,
        payload.distro,
        payload.profile_name,
        payload.playbook_path,
        payload.dry_run,
    )
    return MitigateResponse(job_id=job_id, status=status)


@router.get("/mitigate/history", response_model=list[JobHistoryItem])
def mitigate_history():
    session: Session = get_session()
    with session:
        jobs = session.exec(
            select(MitigationJob).order_by(MitigationJob.created_at.desc())
        ).all()
    return [
        JobHistoryItem(
            id=job.id,
            status=job.status,
            host_count=job.host_count,
            created_at=job.created_at,
        )
        for job in jobs
    ]
