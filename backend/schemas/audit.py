from typing import List

from pydantic import BaseModel


class AuditRequest(BaseModel):
    hosts: List[str]
    distro: str
    profile_name: str
    profile_path: str = ""


class RuleResult(BaseModel):
    rule_id: str
    severity: str
    status: str
    title: str = ""
    description: str = ""
    rationale: str = ""
    fixtext: str = ""


class HostAuditResult(BaseModel):
    host: str
    score: float
    passed: int
    failed: int
    other: int
    rules: List[RuleResult]


class AuditResponse(BaseModel):
    job_id: int
    results: List[HostAuditResult]
