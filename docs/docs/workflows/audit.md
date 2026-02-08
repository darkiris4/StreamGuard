---
sidebar_position: 2
title: Auditing Hosts
---

# Auditing Hosts

An audit scans one or more hosts against a STIG baseline using OpenSCAP and reports every rule as pass, fail, or other.

## End-to-End Walkthrough

### 1. Verify Your Hosts

Go to the **Hosts** page. Hosts from your SSH `known_hosts` are loaded automatically on startup. Verify the target appears in the list. If not, add it manually — enter the hostname, IP, SSH user, and OS distro, then click **Test** to confirm SSH connectivity before saving.

### 2. Ensure CAC Content Is Available

Navigate to the **Audit** page. When you click **Run**, the UI automatically checks whether STIG content is cached for your selected distro. If not, a yellow banner appears:

> **No cached CAC content found for rhel9. Fetch content from ComplianceAsCode first.**

Click **Fetch Now**. StreamGuard downloads the latest ComplianceAsCode release ZIP and extracts the datastream XML and playbooks. This only needs to happen once per version — results are cached.

See [CAC Content](./cac-content.md) for details on Online vs Offline modes.

### 3. Configure the Scan

| Field | Example | Notes |
|---|---|---|
| **Hosts** | `10.0.1.50, 10.0.1.51` | Comma-separated hostnames or IPs |
| **Distro** | `rhel9` | Must match a supported CAC product ID |
| **Profile Name** | `stig` | STIG profile to evaluate against |
| **Profile Path** | *(leave empty)* | Auto-resolved from CAC cache; only set if using a custom file |

### 4. Run the Audit

Click **Run**. Behind the scenes:

1. The backend resolves the datastream path from `cac_cache/metadata.json`.
2. For `localhost` / `127.0.0.1`: runs `oscap xccdf eval` directly.
3. For remote hosts: runs `oscap-ssh user@host 22 xccdf eval ...` over SSH.
4. Scans run in parallel (up to `MAX_CONCURRENT_HOSTS`).
5. Results are parsed from the XCCDF output XML and stored in PostgreSQL.

### 5. Review Results

The data grid shows every rule with:

- **Rule ID** — the XCCDF rule identifier.
- **Severity** — CAT I (high), CAT II (medium), CAT III (low).
- **Status** — pass, fail, error, notapplicable, etc.
- **Host** — which host the result belongs to.

### 6. Check the Dashboard

The **Dashboard** page aggregates results across all hosts:

- **Compliance Gauge** — fleet-wide compliance percentage.
- **Severity Breakdown** — failed rules by CAT I/II/III.
- **Top Failures** — most common failing rules for prioritized remediation.
- **Timeline** — compliance trend over time.

### 7. Export Results

Use the API to export scan results:

```bash
# JSON
curl http://<server-ip>:8000/api/audit/results/{job_id}/export/json

# CSV
curl http://<server-ip>:8000/api/audit/results/{job_id}/export/csv -o results.csv
```

## Tips

- **Test SSH first** — use the "Test" button on the Hosts page before running a large audit.
- **Tune concurrency** — set `MAX_CONCURRENT_HOSTS` in `docker-compose.yml` based on your server and network capacity.
- **Use specific distros** — `rhel9` is better than `rhel` to avoid ambiguity in profile resolution.
- **Re-audit after mitigation** — always run a follow-up scan to verify remediation took effect.
