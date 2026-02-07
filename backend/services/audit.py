import asyncio
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree

from sqlmodel import Session, select

from core.config import settings
from db import get_session
from models.host import Host
from models.job import AuditJob
from models.scan import ScanResult, ScanRuleResult
from schemas.audit import HostAuditResult, RuleResult
from services.ws_manager import manager


ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "scan_results"
_MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_HOSTS", "10"))
_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENT)


def _text_content(element: ElementTree.Element | None) -> str:
    if element is None:
        return ""
    return " ".join(chunk.strip() for chunk in element.itertext() if chunk.strip()).strip()


def _load_rule_metadata(xccdf_path: str) -> Dict[str, RuleResult]:
    metadata: Dict[str, RuleResult] = {}
    if not xccdf_path:
        return metadata
    try:
        tree = ElementTree.parse(xccdf_path)
    except (FileNotFoundError, ElementTree.ParseError):
        return metadata

    root = tree.getroot()
    for rule in root.findall(".//{*}Rule"):
        rule_id = rule.attrib.get("id", "")
        if not rule_id:
            continue
        title = _text_content(rule.find(".//{*}title"))
        description = _text_content(rule.find(".//{*}description"))
        rationale = _text_content(rule.find(".//{*}rationale"))
        fixtext = _text_content(rule.find(".//{*}fixtext"))
        severity = rule.attrib.get("severity", "unknown")
        metadata[rule_id] = RuleResult(
            rule_id=rule_id,
            severity=severity,
            status="unknown",
            title=title,
            description=description,
            rationale=rationale,
            fixtext=fixtext,
        )
    return metadata


def _parse_xccdf_results(
    result_path: Path, benchmark_path: str
) -> Tuple[List[RuleResult], int, int, int]:
    tree = ElementTree.parse(result_path)
    root = tree.getroot()
    namespace = {"xccdf": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}

    metadata = _load_rule_metadata(benchmark_path)
    rules = []
    passed = failed = other = 0

    for rule_result in root.findall(".//{*}rule-result"):
        rule_id = rule_result.attrib.get("idref", "")
        severity = rule_result.attrib.get("severity", "unknown")
        result_text = rule_result.findtext(
            "xccdf:result", default="unknown", namespaces=namespace
        )
        status = result_text.lower()
        if status == "pass":
            passed += 1
        elif status == "fail":
            failed += 1
        else:
            other += 1

        meta = metadata.get(rule_id)
        rules.append(
            RuleResult(
                rule_id=rule_id,
                severity=severity if severity != "unknown" else (meta.severity if meta else "unknown"),
                status=status,
                title=meta.title if meta else "",
                description=meta.description if meta else "",
                rationale=meta.rationale if meta else "",
                fixtext=meta.fixtext if meta else "",
            )
        )

    return rules, passed, failed, other


def _run_oscap_eval(host: str, profile_name: str, xccdf_path: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if host in {"localhost", "127.0.0.1"}:
        command = [
            "oscap",
            "xccdf",
            "eval",
            "--profile",
            profile_name,
            "--results",
            str(output_path),
            xccdf_path,
        ]
    else:
        command = [
            "oscap-ssh",
            host,
            "22",
            settings.ssh_key_path,
            "xccdf",
            "eval",
            "--profile",
            profile_name,
            "--results",
            str(output_path),
            xccdf_path,
        ]

    subprocess.run(command, check=True)


async def run_audit_for_host(
    host: str, distro: str, profile_name: str, profile_path: str, job_id: int
) -> HostAuditResult:
    async with _SEMAPHORE:
        await manager.broadcast(
            str(job_id), {"event": "audit.start", "host": host}
        )
        output_path = ARTIFACTS_DIR / str(job_id) / f"{host}_results.xml"

        await asyncio.to_thread(
            _run_oscap_eval, host, profile_name, profile_path, output_path
        )

        rules, passed, failed, other = _parse_xccdf_results(output_path, profile_path)
        score = 0.0
        total = passed + failed + other
        if total:
            score = round((passed / total) * 100.0, 2)

        session: Session = get_session()
        with session:
            host_row = session.exec(
                select(Host).where(Host.hostname == host)
            ).first()
            if not host_row:
                host_row = Host(hostname=host, ssh_user=settings.ssh_user)
                session.add(host_row)
                session.commit()
                session.refresh(host_row)

            scan_result = ScanResult(
                audit_job_id=job_id,
                host_id=host_row.id,
                distro=distro,
                profile_name=profile_name,
                score=score,
                passed=passed,
                failed=failed,
                other=other,
            )
            session.add(scan_result)
            session.commit()
            session.refresh(scan_result)

            for rule in rules:
                session.add(
                    ScanRuleResult(
                        scan_result_id=scan_result.id,
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        status=rule.status,
                        title=rule.title,
                        description=rule.description,
                        rationale=rule.rationale,
                        fixtext=rule.fixtext,
                    )
                )
            session.commit()

        await manager.broadcast(
            str(job_id), {"event": "audit.complete", "host": host}
        )

        return HostAuditResult(
            host=host,
            score=score,
            passed=passed,
            failed=failed,
            other=other,
            rules=rules,
        )


async def run_audit(
    hosts: List[str], distro: str, profile_name: str, profile_path: str
) -> tuple[int, List[HostAuditResult]]:
    session: Session = get_session()
    with session:
        job = AuditJob(
            distro=distro,
            profile_name=profile_name,
            status="running",
            host_count=len(hosts),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

    tasks = [
        run_audit_for_host(host, distro, profile_name, profile_path, job.id)
        for host in hosts
    ]
    results = await asyncio.gather(*tasks)

    session = get_session()
    with session:
        job = session.get(AuditJob, job.id)
        if job:
            job.status = "completed"
            session.add(job)
            session.commit()

    return job.id, results
