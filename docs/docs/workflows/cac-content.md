---
sidebar_position: 1
title: CAC Content
---

# Fetching ComplianceAsCode Content

Before you can audit or mitigate a host, StreamGuard needs STIG content — datastream XMLs for OpenSCAP and Ansible playbooks for remediation. This content comes from the [ComplianceAsCode](https://github.com/ComplianceAsCode/content) project.

## Online Mode (Default)

In Online mode, StreamGuard downloads content on demand from GitHub releases:

1. Queries the GitHub Releases API for the latest version tag.
2. Downloads `scap-security-guide-{version}.zip`.
3. Extracts datastream files (`ssg-{product}-ds.xml`) and playbooks (`{product}-playbook-{profile}.yml`) to `cac_cache/releases/{version}/`.
4. Writes `cac_cache/metadata.json` to track what's available.

**This happens automatically** — when you click **Run** on the Audit or Mitigate page without a manually-specified path, the UI checks the cache. If content is missing, a "Fetch Now" banner appears. One click downloads everything needed.

The backend will also auto-fetch on demand if you submit an audit/mitigate request and the content isn't cached yet.

## Offline Mode

Toggle the **Cloud/Offline switch** in the top toolbar to switch modes. In Offline mode, StreamGuard uses GitPython to clone (or pull) the full ComplianceAsCode repo to `cac_cache/repo/`. This is useful for:

- Air-gapped environments with no internet access.
- Pinning to a specific repo state for reproducible compliance evidence.
- Development and testing against local content.

Set `OFFLINE_MODE=true` in `docker-compose.yml` to default to offline.

## Checking Cache Status

The toolbar shows a **CAC version chip** (e.g., "CAC 0.1.73") when content is cached. You can also query the API directly:

```bash
curl http://<server-ip>:8000/api/cac/status
```

Returns the current mode, cached version, available distros, and profiles.

## Supported Distros

| Product ID | Family |
|---|---|
| `rhel7`, `rhel8`, `rhel9` | Red Hat Enterprise Linux |
| `fedora` | Fedora |
| `ubuntu2004`, `ubuntu2204`, `ubuntu2404` | Ubuntu |
| `debian11`, `debian12` | Debian |

You can use either the specific product ID (e.g., `rhel9`) or the family name (e.g., `rhel` — fetches all RHEL variants).

## Error Handling

If a fetch fails (network issues, GitHub rate limiting), StreamGuard falls back to whatever is already cached. If nothing is cached, you'll see an error prompting you to retry or switch to offline mode.

## Manual Fetch via API

```bash
# Fetch content for a specific distro
curl http://<server-ip>:8000/api/cac/fetch/rhel9

# List available STIG profiles parsed from cached datastream XML
curl http://<server-ip>:8000/api/cac/profiles/rhel9
```
