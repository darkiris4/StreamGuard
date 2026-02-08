---
sidebar_position: 1
title: Overview
---

# StreamGuard User Guide

StreamGuard is an open-source STIG compliance platform that runs as a centralized Docker Compose stack. From a single server it can reach out to any host on your network — audit them against DISA STIG baselines using OpenSCAP, then remediate failures with Ansible playbooks sourced directly from the ComplianceAsCode project.

## How It Works

```mermaid
flowchart LR
    subgraph streamguard["StreamGuard (Single Docker Compose Stack)"]
        direction TB
        FE["Frontend :3000"]
        BE["Backend :8000 (FastAPI + oscap-ssh + ansible-runner + CAC fetch)"]
        DB["PostgreSQL :5432"]

        FE -->|"/api proxy"| BE
        BE -->|"results & jobs"| DB

        subgraph tools["Internal Backend Tools (all run inside backend container)"]
            direction LR
            CAC["CAC fetch (GitHub / cache)"]
            OSCAP["oscap-ssh (audit)"]
            ANS["ansible-runner (mitigate)"]
        end

        BE --> CAC
        BE --> OSCAP
        BE --> ANS
    end

    subgraph targets["Target Hosts on LAN"]
        direction TB
        H1["RHEL 8/9"]
        H2["Ubuntu 22.04"]
        H3["Debian 12"]
    end

    OSCAP -->|"SSH :22"| H1 & H2 & H3
    ANS -->|"SSH :22"| H1 & H2 & H3

    CAC -. "HTTPS" .-> GH["GitHub ComplianceAsCode"]

    linkStyle default stroke:#aaa,stroke-width:2.5px

    style streamguard fill:#1a1a2e,stroke:#16213e,color:#e0e0e0
    style targets fill:#1a1a2e,stroke:#533483,color:#e0e0e0
    style GH fill:#0d1117,stroke:#30363d,color:#e0e0e0

    style FE fill:#1565c0,stroke:#0d47a1,color:#fff
    style BE fill:#2e7d32,stroke:#1b5e20,color:#fff
    style DB fill:#6a1b9a,stroke:#4a148c,color:#fff

    style CAC fill:#00695c,stroke:#004d40,color:#fff
    style OSCAP fill:#e65100,stroke:#bf360c,color:#fff
    style ANS fill:#e65100,stroke:#bf360c,color:#fff
```

## Key Capabilities

- **Live CAC integration** — fetches ComplianceAsCode release ZIPs on demand from GitHub, or works fully offline with a local git clone.
- **Multi-host auditing** — runs OpenSCAP XCCDF scans in parallel across your fleet over SSH.
- **Automated remediation** — applies Ansible playbooks from ComplianceAsCode with dry-run support.
- **SSH host discovery** — auto-discovers hosts from your `~/.ssh/known_hosts` on startup.
- **Dashboard & reporting** — compliance gauges, severity breakdowns, trend timelines, and CSV/JSON export.
- **Hardened ISOs** — generates kickstart/preseed ISOs for clean STIG-compliant installs.
- **Custom profiles** — tailor STIG enforcement with the built-in Monaco editor.

## Prerequisites

- **Docker Engine + Docker Compose** on the central server.
- **SSH key-based access** to every target host you want to audit or mitigate. The server's `~/.ssh/` directory is mounted into the backend container.
- **Basic familiarity** with STIG severity levels (CAT I / II / III), OpenSCAP, and Ansible.

## Quick Start

```bash
git clone <repo-url> StreamGuard && cd StreamGuard
cp .env.example .env          # edit if needed
docker compose up -d
```

Then open the UI at `http://<server-ip>:3000`. Hosts from your SSH `known_hosts` are loaded automatically — go to **Audit**, pick a distro and profile, and click **Run**.

See the [Setup](./setup.md) page for detailed configuration.
