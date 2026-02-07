from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ScanResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    audit_job_id: Optional[int] = Field(default=None, foreign_key="auditjob.id")
    host_id: Optional[int] = Field(default=None, foreign_key="host.id")
    distro: str
    profile_name: str
    score: float = 0.0
    passed: int = 0
    failed: int = 0
    other: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScanRuleResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scan_result_id: Optional[int] = Field(
        default=None, foreign_key="scanresult.id"
    )
    rule_id: str
    severity: str
    status: str
    title: str = ""
    description: str = ""
    rationale: str = ""
    fixtext: str = ""
