---
sidebar_position: 1
title: Overview
---

# StreamGuard User Guide

StreamGuard is an open-source compliance dashboard built for **DevSecOps** and **cybersecurity** teams working with **STIG** baselines. It provides a modern UI for ComplianceAsCode (CAC) content, multi-host auditing and remediation, hardened ISO generation, and evidence-grade reporting.

## Key Capabilities
- **Live CAC integration** or offline cached content.
- **Parallel auditing** with OpenSCAP and XCCDF results.
- **Mitigations** via Ansible playbooks with dry-run support.
- **Hardened ISOs** (kickstart/preseed) for clean installs.
- **Custom profiles** to tailor STIG enforcement.
- **Dashboards & exports** for operational visibility.

## Assumptions
- You have basic familiarity with **Ansible** and **OpenSCAP**.
- You can access target hosts via **passwordless SSH**.
- You understand STIG severity levels (CAT I/II/III).

Use this guide to get StreamGuard running, build repeatable workflows, and integrate it into your compliance pipeline.
