---
sidebar_position: 1
title: CAC Content
---

# Fetching ComplianceAsCode Content

Before you can audit or mitigate a host, StreamGuard needs STIG content — datastream XMLs for OpenSCAP and Ansible playbooks for remediation. This content comes from the [ComplianceAsCode](https://github.com/ComplianceAsCode/content) project.

## Online Mode (Default)

In Online mode, StreamGuard separates **profile browsing** from **artifact downloads**:

### 1) Live profile browsing (no upfront fetch)

When you select a distro in the Audit or Mitigate UI, StreamGuard fetches the
profile list directly from the ComplianceAsCode GitHub repo using the
GitHub Contents API (`products/{product}/profiles`). This gives you a live,
up-to-date list of profiles without downloading any large content bundles.

### 2) Auto-download artifacts on Run

When you click **Run** (Audit or Mitigate) and no explicit path is provided,
the backend auto-downloads the latest release ZIP and caches the artifacts:

1. Queries the GitHub Releases API for the latest version tag.
2. Downloads `scap-security-guide-{version}.zip`.
3. Extracts datastream files (`ssg-{product}-ds.xml`) and playbooks
   (`{product}-playbook-{profile}.yml`) to `cac_cache/releases/{version}/`.
4. Writes `cac_cache/metadata.json` to track what's available.

## Offline Mode

Toggle the **Cloud/Offline switch** in the top toolbar to switch modes. In Offline mode, StreamGuard uses GitPython to clone (or pull) the full ComplianceAsCode repo to `cac_cache/repo/`. This is useful for:

- Air-gapped environments with no internet access.
- Pinning to a specific repo state for reproducible compliance evidence.
- Development and testing against local content.

Set `OFFLINE_MODE=true` in `docker-compose.yml` to default to offline.

## Checking Cache Status

The toolbar shows a **CAC version chip** (e.g., "CAC 0.1.73") when artifacts
are cached. Profile lists will still load in Online mode even if the cache is
empty, because they are fetched live from GitHub.

You can also query the API directly:

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

## Error Handling and Fallbacks

Profile resolution follows this order:

1. **Live GitHub API** (Contents API + raw YAML)
2. **Cached datastream XML** (if artifacts are already cached)
3. **Emergency fallback list** (minimal profiles to keep the UI usable)

If a fetch fails (network issues, GitHub rate limiting), StreamGuard falls back
to whatever is already cached. If nothing is cached, the emergency list is used
for browsing until connectivity is restored.

### GitHub Rate Limits

- **Unauthenticated:** 60 requests per hour
- **Authenticated (recommended):** 5000 requests per hour

Set `GITHUB_TOKEN` in `docker-compose.yml` for higher limits.

## Manual Fetch via API

```bash
# Fetch content for a specific distro
curl http://<server-ip>:8000/api/cac/fetch/rhel9

# List available STIG profiles (live from GitHub in Online mode)
curl http://<server-ip>:8000/api/cac/profiles/rhel9
```
