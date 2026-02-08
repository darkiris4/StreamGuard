import csv
import io

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sqlmodel import Session, select

from db import get_session
from models.job import AuditJob
from models.scan import ScanResult, ScanRuleResult
from schemas.job import JobHistoryItem

from schemas.audit import AuditRequest, AuditResponse
from services.audit import run_audit
from services.cac_fetch import ensure_cac_content, resolve_content_paths


router = APIRouter(tags=["audit"])


@router.post("/audit", response_model=AuditResponse)
async def audit_hosts(payload: AuditRequest):
    # Auto-resolve profile_path from CAC cache when not provided
    if not payload.profile_path:
        ds_path, _ = resolve_content_paths(payload.distro, payload.profile_name)
        if not ds_path:
            # Attempt to fetch content on demand
            await ensure_cac_content(payload.distro)
            ds_path, _ = resolve_content_paths(payload.distro, payload.profile_name)
        if ds_path:
            payload.profile_path = ds_path
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No CAC content available for this distro. "
                    "Fetch content first via /api/cac/fetch/{distro}."
                ),
            )
    job_id, results = await run_audit(
        payload.hosts, payload.distro, payload.profile_name, payload.profile_path
    )
    return AuditResponse(job_id=job_id, results=results)


@router.get("/audit/history", response_model=list[JobHistoryItem])
def audit_history():
    session: Session = get_session()
    with session:
        jobs = session.exec(select(AuditJob).order_by(AuditJob.created_at.desc())).all()
    return [
        JobHistoryItem(
            id=job.id,
            status=job.status,
            host_count=job.host_count,
            created_at=job.created_at,
        )
        for job in jobs
    ]


@router.get("/audit/results/{job_id}/export/{format}")
def export_audit_results(job_id: int, format: str):
    session: Session = get_session()
    with session:
        results = session.exec(
            select(
                ScanResult.id,
                ScanResult.host_id,
                ScanRuleResult.rule_id,
                ScanRuleResult.severity,
                ScanRuleResult.status,
                ScanRuleResult.title,
                ScanRuleResult.description,
                ScanRuleResult.rationale,
                ScanRuleResult.fixtext,
            )
            .join(ScanRuleResult, ScanRuleResult.scan_result_id == ScanResult.id)
            .where(ScanResult.audit_job_id == job_id)
        ).all()

    rows = [
        {
            "scan_result_id": scan_id,
            "host_id": host_id,
            "rule_id": rule_id,
            "severity": severity,
            "status": status,
            "title": title,
            "description": description,
            "rationale": rationale,
            "fixtext": fixtext,
        }
        for (
            scan_id,
            host_id,
            rule_id,
            severity,
            status,
            title,
            description,
            rationale,
            fixtext,
        ) in results
    ]

    if format.lower() == "json":
        return rows

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys() if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_results.csv"},
        )

    raise HTTPException(status_code=400, detail="Unsupported export format")
