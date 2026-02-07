import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Optional

import requests


ISO_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "isos"
WORK_DIR = Path(__file__).resolve().parents[1] / "iso_workdir"


def _write_hardening_hook(extract_dir: Path) -> Path:
    hook_dir = extract_dir / "streamguard"
    hook_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hook_dir / "hardening.sh"
    hook_path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
echo "StreamGuard STIG hardening hook start" > /var/log/streamguard-hardening.log
# TODO: pull CAC playbooks or apply local hardening bundle
echo "StreamGuard STIG hardening hook complete" >> /var/log/streamguard-hardening.log
"""
    )
    hook_path.chmod(0o755)
    return hook_path


def _write_kickstart(distro: str, content_path: Path) -> None:
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# StreamGuard kickstart for {distro}
lang en_US.UTF-8
keyboard us
timezone UTC
rootpw --plaintext changeme
reboot
%packages
@^minimal-environment
%end
%post --log=/root/streamguard-hardening.log
if [ -x /run/install/repo/streamguard/hardening.sh ]; then
  /run/install/repo/streamguard/hardening.sh
fi
%end
"""
    content_path.write_text(content)


def _write_preseed(distro: str, content_path: Path) -> None:
    content_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# StreamGuard preseed for {distro}
d-i debian-installer/locale string en_US.UTF-8
d-i keyboard-configuration/xkb-keymap select us
d-i time/zone string UTC
d-i passwd/root-password password changeme
d-i passwd/root-password-again password changeme
d-i finish-install/reboot_in_progress note
d-i preseed/late_command string if [ -x /cdrom/streamguard/hardening.sh ]; then /cdrom/streamguard/hardening.sh; fi
"""
    content_path.write_text(content)


def _write_autoinstall_cloud_init(extract_dir: Path) -> None:
    nocloud_dir = extract_dir / "nocloud"
    nocloud_dir.mkdir(parents=True, exist_ok=True)
    user_data = """#cloud-config
autoinstall:
  version: 1
  identity:
    hostname: streamguard
    username: streamguard
    password: "$6$rounds=4096$streamguard$y3v1ST1g0cXvQqK1k4lq6vrr2kK9a4hn3r5xXfA8t5u8mW0S8n1kAk2OTglG2x1S0mQk6bC1ZxE9i1"
  late-commands:
    - curtin in-target -- /bin/bash -c 'if [ -x /cdrom/streamguard/hardening.sh ]; then /cdrom/streamguard/hardening.sh; fi'
"""
    meta_data = "instance-id: streamguard\nlocal-hostname: streamguard\n"
    (nocloud_dir / "user-data").write_text(user_data)
    (nocloud_dir / "meta-data").write_text(meta_data)


def _download_iso(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with dest.open("wb") as out:
            shutil.copyfileobj(response.raw, out)


def _extract_iso(base_iso: Path, extract_dir: Path) -> None:
    extract_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "xorriso",
            "-osirrox",
            "on",
            "-indev",
            str(base_iso),
            "-extract",
            "/",
            str(extract_dir),
        ],
        check=True,
    )


def _update_boot_config(path: Path, token: str) -> None:
    if not path.exists():
        return
    lines = path.read_text().splitlines()
    updated = []
    for line in lines:
        if token in line:
            updated.append(line)
            continue
        if line.strip().startswith("append "):
            updated.append(f"{line} {token}")
        elif line.strip().startswith("linux "):
            updated.append(f"{line} {token}")
        else:
            updated.append(line)
    path.write_text("\n".join(updated) + "\n")


def _rebuild_iso(extract_dir: Path, output_iso: Path) -> None:
    subprocess.run(
        [
            "xorriso",
            "-as",
            "mkisofs",
            "-r",
            "-J",
            "-l",
            "-V",
            "StreamGuard",
            "-o",
            str(output_iso),
            str(extract_dir),
        ],
        check=True,
    )


def build_iso(
    distro: str, base_iso_path: Optional[Path] = None, base_iso_url: str = ""
) -> Path:
    ISO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    output_iso = ISO_OUTPUT_DIR / f"{distro}_stig_{uuid.uuid4().hex}.iso"
    work_id = uuid.uuid4().hex
    extract_dir = WORK_DIR / f"{distro}_{work_id}"

    if base_iso_path:
        base_iso = base_iso_path
    elif base_iso_url:
        base_iso = WORK_DIR / f"{distro}_base_{work_id}.iso"
        _download_iso(base_iso_url, base_iso)
    else:
        raise ValueError("Base ISO path or URL is required")

    _extract_iso(base_iso, extract_dir)

    _write_hardening_hook(extract_dir)

    if distro in {"rhel", "fedora"}:
        ks_path = extract_dir / "ks.cfg"
        _write_kickstart(distro, ks_path)
        _update_boot_config(
            extract_dir / "isolinux" / "isolinux.cfg", "inst.ks=cdrom:/ks.cfg"
        )
        _update_boot_config(
            extract_dir / "boot" / "grub" / "grub.cfg", "inst.ks=cdrom:/ks.cfg"
        )
    elif distro == "ubuntu":
        preseed_path = extract_dir / "preseed.cfg"
        _write_preseed(distro, preseed_path)
        _write_autoinstall_cloud_init(extract_dir)
        _update_boot_config(
            extract_dir / "isolinux" / "isolinux.cfg",
            "auto=true priority=critical preseed/file=/cdrom/preseed.cfg",
        )
        _update_boot_config(
            extract_dir / "boot" / "grub" / "grub.cfg",
            "auto=true priority=critical preseed/file=/cdrom/preseed.cfg",
        )
        _update_boot_config(
            extract_dir / "isolinux" / "isolinux.cfg",
            "autoinstall ds=nocloud\\;s=/cdrom/nocloud/",
        )
        _update_boot_config(
            extract_dir / "boot" / "grub" / "grub.cfg",
            "autoinstall ds=nocloud\\;s=/cdrom/nocloud/",
        )
    else:
        preseed_path = extract_dir / "preseed.cfg"
        _write_preseed(distro, preseed_path)
        _update_boot_config(
            extract_dir / "isolinux" / "isolinux.cfg",
            "auto=true priority=critical preseed/file=/cdrom/preseed.cfg",
        )
        _update_boot_config(
            extract_dir / "boot" / "grub" / "grub.cfg",
            "auto=true priority=critical preseed/file=/cdrom/preseed.cfg",
        )

    _rebuild_iso(extract_dir, output_iso)
    shutil.rmtree(extract_dir, ignore_errors=True)

    return output_iso
