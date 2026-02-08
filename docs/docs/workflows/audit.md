---
title: Auditing Hosts
---

# Auditing Hosts

## Workflow
1. Add your hosts under **Hosts**.
2. Fetch CAC content (live or offline cached).
3. Open the **Audit** page.
4. Provide target hosts, distro, and profile path.
5. Run the scan and monitor progress.

## Outputs
- Rule-level results with status, severity, and metadata
- Dashboard summaries (fleet score, severity breakdown)
- Exportable JSON/CSV results

## Tips
- Use `MAX_CONCURRENT_HOSTS` to control scan pressure.
- Test SSH connectivity before large runs.
