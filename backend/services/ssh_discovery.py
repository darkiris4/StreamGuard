"""Discover SSH hosts from the mounted ~/.ssh/ directory on startup.

Parses ``~/.ssh/config`` for Host entries and ``known_hosts`` for unhashed
hostnames, then upserts them into the Host table so they appear in the UI
immediately after a fresh ``docker compose up``.

Note: Most modern Linux distros hash ``known_hosts`` by default
(``HashKnownHosts yes``), making those entries unreadable.  The SSH config
file is the more reliable discovery source.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple

from sqlmodel import Session, select

from core.config import settings
from db import get_session
from models.host import Host

logger = logging.getLogger(__name__)

SSH_DIR = Path("/app/ssh")
SSH_CONFIG_PATH = SSH_DIR / "config"
KNOWN_HOSTS_PATH = SSH_DIR / "known_hosts"

_HASHED_RE = re.compile(r"^\|1\|")
_WILDCARD_RE = re.compile(r"[*?]")

# Hosts to never import
_SKIP_HOSTS = {"localhost", "127.0.0.1", "::1", "*"}


# ---------------------------------------------------------------------------
# SSH config parser
# ---------------------------------------------------------------------------


def _parse_ssh_config() -> List[Dict[str, str]]:
    """Parse ``~/.ssh/config`` and return a list of host entries.

    Each entry is a dict with keys like ``host`` (the alias), ``hostname``
    (the real address), ``user``, ``port``, ``identityfile``.
    """
    if not SSH_CONFIG_PATH.exists():
        logger.info("No SSH config at %s — skipping config-based discovery", SSH_CONFIG_PATH)
        return []

    entries: List[Dict[str, str]] = []
    current: Dict[str, str] | None = None

    for line in SSH_CONFIG_PATH.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Split on first whitespace: "Host myserver" → ("Host", "myserver")
        parts = stripped.split(None, 1)
        if len(parts) < 2:
            continue
        key, value = parts[0].lower(), parts[1].strip()

        if key == "host":
            # Each "Host" directive starts a new block
            # Can have multiple aliases: "Host foo bar"
            aliases = value.split()
            for alias in aliases:
                if alias in _SKIP_HOSTS or _WILDCARD_RE.search(alias):
                    continue
                current = {"host": alias}
                entries.append(current)
        elif current is not None:
            # Accumulate directives under the current Host block
            current[key] = value

    return entries


def _resolve_hostname(entry: Dict[str, str]) -> str:
    """Resolve the actual hostname/IP from an SSH config entry.

    Handles ``%h`` substitution (replaced with the Host alias).
    If no ``HostName`` is specified, the alias itself is the hostname.
    """
    alias = entry.get("host", "")
    raw = entry.get("hostname", alias)
    # %h is substituted with the original Host alias
    return raw.replace("%h", alias)


# ---------------------------------------------------------------------------
# known_hosts parser (for unhashed entries only)
# ---------------------------------------------------------------------------


def _parse_known_hosts() -> List[str]:
    """Parse known_hosts and return hostnames from unhashed entries.

    Hashed entries (``|1|...``) are skipped — they cannot be reversed.
    """
    if not KNOWN_HOSTS_PATH.exists():
        logger.info("No known_hosts at %s", KNOWN_HOSTS_PATH)
        return []

    hosts: set[str] = set()
    hashed_count = 0

    for line in KNOWN_HOSTS_PATH.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if _HASHED_RE.match(line):
            hashed_count += 1
            continue
        # First field is hostname(s), possibly comma-separated
        host_field = line.split()[0]
        for entry in host_field.split(","):
            entry = entry.strip()
            if not entry:
                continue
            # Strip [brackets]:port notation
            if entry.startswith("["):
                entry = entry.split("]")[0].lstrip("[")
            if entry not in _SKIP_HOSTS:
                hosts.add(entry)

    if hashed_count and not hosts:
        logger.info(
            "known_hosts contains %d entries but all are hashed "
            "(HashKnownHosts is enabled). Using SSH config for discovery instead.",
            hashed_count,
        )
    elif hashed_count:
        logger.info(
            "known_hosts: found %d unhashed hosts, skipped %d hashed entries",
            len(hosts),
            hashed_count,
        )

    return sorted(hosts)


# ---------------------------------------------------------------------------
# Key detection
# ---------------------------------------------------------------------------


def _detect_ssh_key() -> str:
    """Find the first usable SSH private key in the mounted directory."""
    preferred = ["id_ed25519", "id_rsa", "id_ecdsa", "id_dsa"]
    for name in preferred:
        key_path = SSH_DIR / name
        if key_path.exists():
            return str(key_path)
    # Check for any key named id_ed25519_* (custom named keys)
    for path in sorted(SSH_DIR.glob("id_*")):
        # Skip .pub files
        if path.suffix == ".pub":
            continue
        return str(path)
    return settings.ssh_key_path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sync_known_hosts_to_db() -> Tuple[int, int]:
    """Discover hosts from SSH config and known_hosts, upsert into database.

    Returns ``(discovered, created)`` counts.
    """
    # 1. Parse SSH config (primary source — always has plaintext hostnames)
    config_entries = _parse_ssh_config()

    # 2. Parse known_hosts (secondary — only useful if not hashed)
    known_hostnames = _parse_known_hosts()

    # 3. Detect the best available SSH key
    default_key = _detect_ssh_key()

    # Build a merged list: config entries are richer (have user, key, port)
    # known_hosts entries are hostname-only
    to_import: Dict[str, Dict[str, str]] = {}

    for entry in config_entries:
        hostname = _resolve_hostname(entry)
        if hostname and hostname not in _SKIP_HOSTS:
            to_import[hostname] = entry

    for hostname in known_hostnames:
        if hostname not in to_import:
            to_import[hostname] = {"host": hostname}

    if not to_import:
        logger.info("SSH host discovery: no hosts found to import")
        return 0, 0

    # 4. Upsert into database
    session: Session = get_session()
    created = 0
    updated = 0
    with session:
        existing_hosts = {
            h.hostname: h for h in session.exec(select(Host)).all()
        }
        # Also index by alias for duplicate checks
        existing_aliases = {
            h.alias: h for h in existing_hosts.values() if h.alias
        }

        for hostname, entry in to_import.items():
            alias = entry.get("host", hostname)

            # Resolve per-host SSH key if specified in config
            identity = entry.get("identityfile", "")
            if identity:
                identity = identity.replace("~/.ssh/", str(SSH_DIR) + "/")
                identity = identity.replace("$HOME/.ssh/", str(SSH_DIR) + "/")

            # Parse port
            port = 22
            if entry.get("port"):
                try:
                    port = int(entry["port"])
                except ValueError:
                    pass

            # Check if this host already exists — update it with fresh config data
            existing = existing_hosts.get(hostname) or existing_aliases.get(alias)
            if existing:
                changed = False
                if not existing.alias and alias:
                    existing.alias = alias
                    changed = True
                if not existing.identity_file and (identity or default_key):
                    existing.identity_file = identity or default_key
                    changed = True
                if existing.port == 22 and port != 22:
                    existing.port = port
                    changed = True
                if not existing.proxy_jump and entry.get("proxyjump"):
                    existing.proxy_jump = entry["proxyjump"]
                    changed = True
                if existing.ssh_user == "root" and entry.get("user"):
                    existing.ssh_user = entry["user"]
                    changed = True
                if changed:
                    existing.source = "ssh_config"
                    session.add(existing)
                    updated += 1
                continue

            host = Host(
                alias=alias,
                hostname=hostname,
                ssh_user=entry.get("user", settings.ssh_user),
                port=port,
                identity_file=identity or default_key,
                proxy_jump=entry.get("proxyjump", ""),
                ssh_key_path=identity or default_key,
                source="ssh_config",
            )
            session.add(host)
            created += 1
            existing_hosts[hostname] = host

        if created or updated:
            session.commit()

    logger.info(
        "SSH host discovery: found %d hosts (%d from config, %d from known_hosts), "
        "created %d new, updated %d existing",
        len(to_import),
        len(config_entries),
        len(known_hostnames),
        created,
        updated,
    )
    return len(to_import), created
