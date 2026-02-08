---
sidebar_position: 3
title: Mitigation
---

# Mitigating Hosts

Mitigation applies Ansible playbooks from ComplianceAsCode to fix STIG failures found during an audit.

## End-to-End Walkthrough

### 1. Review Audit Results

Before mitigating, run an [audit](./audit.md) first. Review the failing rules in the data grid and on the Dashboard. This gives you a clear picture of what will be changed.

### 2. Ensure Playbooks Are Cached

The CAC fetch downloads both datastream XMLs (for auditing) and Ansible playbooks (for mitigation). If you already fetched content for auditing, the playbooks are already there.

If not, the Mitigate page shows the same "Fetch Now" banner as the Audit page. Click it to download content.

### 3. Configure the Remediation

| Field | Example | Notes |
|---|---|---|
| **Hosts** | `10.0.1.50, 10.0.1.51` | Same hosts you audited |
| **Distro** | `rhel9` | Must match the audit distro |
| **Profile Name** | `stig` | Resolves to `rhel9-playbook-stig.yml` from the cache |
| **Playbook Path** | *(leave empty)* | Auto-resolved from CAC cache; only set for custom playbooks |

### 4. Run with Dry-Run First

Click **Run**. By default, mitigation runs in **dry-run mode** (`ansible --check`), which shows what *would* change without actually modifying anything. Review the live logs to understand the scope of changes.

### 5. Monitor Live Logs

The Mitigate page streams Ansible output in real time over WebSocket. You'll see each task's status as it runs across your hosts.

### 6. Apply Fixes

Once you're satisfied with the dry-run output, change `dry_run` to `false` in the API call (or update the UI toggle when available) to apply the actual remediation:

```bash
curl -X POST http://<server-ip>:8000/api/mitigate \
  -H "Content-Type: application/json" \
  -d '{
    "hosts": ["10.0.1.50"],
    "distro": "rhel9",
    "profile_name": "stig",
    "playbook_path": "",
    "dry_run": false
  }'
```

### 7. Re-Audit

After mitigation completes, go back to the **Audit** page and run the scan again. Compare scores — you should see improved compliance. The Dashboard timeline will show the improvement trend.

## The Full Cycle

```
Audit → Review failures → Mitigate (dry-run) → Review changes
  → Mitigate (apply) → Re-Audit → Verify improvement
```

Repeat this cycle, focusing on the highest-severity (CAT I) failures first.

## Best Practices

- **Always dry-run first.** Review every change before applying to production hosts.
- **Batch by severity.** Fix CAT I rules first, re-audit, then move to CAT II/III.
- **Schedule maintenance windows.** Some STIG remediations restart services or change network configuration.
- **Keep evidence.** Export audit results before and after mitigation for compliance documentation.
- **Test on a single host.** Before rolling out to the fleet, mitigate one host and verify it still functions correctly.
