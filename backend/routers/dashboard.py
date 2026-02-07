from datetime import date, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import func
from sqlmodel import Session, select

from db import get_session
from models.host import Host
from models.scan import ScanResult, ScanRuleResult


router = APIRouter(tags=["dashboard"])


def _normalize_severity(severity: str) -> str:
    sev = (severity or "").lower()
    if sev in {"high", "cat1", "critical"}:
        return "high"
    if sev in {"medium", "cat2"}:
        return "medium"
    if sev in {"low", "cat3"}:
        return "low"
    return "low"


@router.get("/dashboard/summary")
def dashboard_summary():
    session: Session = get_session()
    with session:
        total_hosts = session.exec(select(func.count(Host.id))).one()
        latest_per_host = (
            select(
                ScanResult.host_id,
                func.max(ScanResult.created_at).label("max_created"),
            )
            .where(ScanResult.host_id.is_not(None))
            .group_by(ScanResult.host_id)
            .subquery()
        )
        latest_scores = session.exec(
            select(func.avg(ScanResult.score))
            .join(
                latest_per_host,
                (ScanResult.host_id == latest_per_host.c.host_id)
                & (ScanResult.created_at == latest_per_host.c.max_created),
            )
        ).one()
        fallback_score = session.exec(select(func.avg(ScanResult.score))).one()
        fleet_score = float(latest_scores or fallback_score or 0.0)

        critical_fails = session.exec(
            select(func.count(ScanRuleResult.id)).where(
                (ScanRuleResult.status == "fail")
                & (
                    ScanRuleResult.severity.in_(["high", "cat1", "critical"])
                )
            )
        ).one()

    return {
        "fleet_score": round(fleet_score, 2),
        "total_hosts": int(total_hosts or 0),
        "critical_fails": int(critical_fails or 0),
    }


@router.get("/dashboard/severity-breakdown")
def severity_breakdown():
    session: Session = get_session()
    with session:
        results = session.exec(
            select(ScanRuleResult.severity, func.count(ScanRuleResult.id))
            .where(ScanRuleResult.status == "fail")
            .group_by(ScanRuleResult.severity)
        ).all()

    breakdown = {"high": 0, "medium": 0, "low": 0}
    for severity, count in results:
        bucket = _normalize_severity(severity or "")
        breakdown[bucket] += int(count or 0)
    return breakdown


@router.get("/dashboard/top-failures")
def top_failures():
    session: Session = get_session()
    with session:
        results = session.exec(
            select(
                ScanRuleResult.rule_id,
                ScanRuleResult.title,
                func.count(ScanRuleResult.id).label("fail_count"),
            )
            .where(ScanRuleResult.status == "fail")
            .group_by(ScanRuleResult.rule_id, ScanRuleResult.title)
            .order_by(func.count(ScanRuleResult.id).desc())
            .limit(10)
        ).all()

    return [
        {"rule_id": rule_id, "title": title, "count": int(count or 0)}
        for rule_id, title, count in results
    ]


@router.get("/dashboard/timeline")
def timeline():
    end_date = date.today()
    start_date = end_date - timedelta(days=29)

    session: Session = get_session()
    with session:
        results = session.exec(
            select(
                func.date(ScanResult.created_at),
                func.avg(ScanResult.score),
            )
            .where(ScanResult.created_at >= datetime.combine(start_date, datetime.min.time()))
            .group_by(func.date(ScanResult.created_at))
        ).all()

    score_map = {}
    for row_date, avg in results:
        if isinstance(row_date, str):
            key = date.fromisoformat(row_date)
        else:
            key = row_date
        score_map[key] = float(avg or 0.0)
    series = []
    for offset in range(30):
        day = start_date + timedelta(days=offset)
        series.append(
            {"date": day.isoformat(), "score": round(score_map.get(day, 0.0), 2)}
        )
    return series
