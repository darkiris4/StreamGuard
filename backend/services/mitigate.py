import asyncio
import os
from typing import List

import ansible_runner
from sqlmodel import Session

from core.config import settings
from db import get_session
from models.job import MitigationJob
from services.ws_manager import manager


_MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT_HOSTS", "10"))
_SEMAPHORE = asyncio.Semaphore(_MAX_CONCURRENT)
def _emit(job_id: str, payload: dict) -> None:
    asyncio.run(manager.broadcast(job_id, payload))


def _run_ansible(
    job_id: str,
    playbook_path: str,
    inventory: str,
    hosts: List[str],
    dry_run: bool,
) -> None:
    extravars = {"target_hosts": hosts}
    envvars = {}
    if settings.ssh_key_path:
        envvars["ANSIBLE_PRIVATE_KEY_FILE"] = settings.ssh_key_path

    def event_handler(event):
        _emit(job_id, {"event": "mitigate.event", "data": event})

    def status_handler(status_data, runner_config):
        _emit(job_id, {"event": "mitigate.status", "data": status_data})

    runner_thread, runner = ansible_runner.run_async(
        private_data_dir=".",
        playbook=playbook_path,
        inventory=inventory,
        extravars=extravars,
        envvars=envvars,
        event_handler=event_handler,
        status_handler=status_handler,
        quiet=True,
        cmdline="--check" if dry_run else None,
    )
    runner_thread.join()
    _emit(job_id, {"event": "mitigate.complete", "status": runner.status})


async def run_mitigation(
    hosts: List[str],
    distro: str,
    profile_name: str,
    playbook_path: str,
    dry_run: bool,
) -> tuple[int, str]:
    async with _SEMAPHORE:
        session: Session = get_session()
        with session:
            job = MitigationJob(
                distro=distro,
                profile_name=profile_name,
                dry_run=dry_run,
                status="running",
                host_count=len(hosts),
            )
            session.add(job)
            session.commit()
            session.refresh(job)

        inventory = settings.ansible_inventory or ",".join(hosts) + ","

        await asyncio.to_thread(
            _run_ansible, str(job.id), playbook_path, inventory, hosts, dry_run
        )

        session = get_session()
        with session:
            job = session.get(MitigationJob, job.id)
            if job:
                job.status = "completed"
                session.add(job)
                session.commit()

        return job.id, "completed"
