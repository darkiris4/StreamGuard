from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from db import get_session
from models.job import MitigationJob
from schemas.job import JobHistoryItem

from schemas.mitigate import MitigateRequest, MitigateResponse
from services.cac_fetch import ensure_cac_content, resolve_content_paths
from services.mitigate import run_mitigation


router = APIRouter(tags=["mitigate"])


@router.post("/mitigate", response_model=MitigateResponse)
async def mitigate_hosts(payload: MitigateRequest):
    # Auto-resolve playbook_path from CAC cache when not provided
    if not payload.playbook_path:
        _, pb_path = resolve_content_paths(payload.distro, payload.profile_name)
        if not pb_path:
            # Attempt to fetch content on demand
            await ensure_cac_content(payload.distro)
            _, pb_path = resolve_content_paths(payload.distro, payload.profile_name)
        if pb_path:
            payload.playbook_path = pb_path
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No CAC playbook available for this distro/profile. "
                    "Fetch content first via /api/cac/fetch/{distro}."
                ),
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
