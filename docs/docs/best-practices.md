---
title: Best Practices
---

# Best Practices for STIG Compliance

## Enterprise Workflow
- Use offline CAC caching for deterministic content.
- Pin profiles for repeatable evidence.
- Run audits on schedules (CI/CD or cron).
- Treat scan outputs as evidence artifacts.

## Security Considerations
- Store SSH keys securely and rotate regularly.
- Limit remediation to a controlled window.
- Use dry-run to validate changes before apply.

## Performance
- Tune `MAX_CONCURRENT_HOSTS` to avoid saturation.
- Separate scanning and remediation windows.
