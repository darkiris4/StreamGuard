from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from db import get_session
from main import app
from models.host import Host
from models.job import AuditJob
from models.scan import ScanResult, ScanRuleResult


client = TestClient(app)


def test_dashboard_endpoints():
    session = get_session()
    with session:
        host = Host(hostname="host-1", ssh_user="root")
        session.add(host)
        session.commit()
        session.refresh(host)

        job = AuditJob(
            status="completed",
            distro="rhel",
            profile_name="stig",
            host_count=1,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        scan = ScanResult(
            audit_job_id=job.id,
            host_id=host.id,
            distro="rhel",
            profile_name="stig",
            score=85.0,
            passed=10,
            failed=2,
            other=0,
            created_at=datetime.utcnow() - timedelta(days=1),
        )
        session.add(scan)
        session.commit()
        session.refresh(scan)

        session.add(
            ScanRuleResult(
                scan_result_id=scan.id,
                rule_id="V-1",
                severity="high",
                status="fail",
                title="Disable root login",
            )
        )
        session.commit()

    summary = client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["total_hosts"] >= 1

    severity = client.get("/api/dashboard/severity-breakdown")
    assert severity.status_code == 200
    assert severity.json()["high"] >= 1

    top_failures = client.get("/api/dashboard/top-failures")
    assert top_failures.status_code == 200
    assert len(top_failures.json()) >= 1

    timeline = client.get("/api/dashboard/timeline")
    assert timeline.status_code == 200
    assert len(timeline.json()) == 30
