---
title: Setup
---

# Setup and Installation

## Prerequisites
- Docker Engine + Docker Compose
- SSH key for passwordless host access
- Supported distros: **RHEL**, **Fedora**, **Ubuntu**, **Debian**

## Docker Compose (Recommended)
1. Copy `.env.example` to `.env` and update values.
2. Mount your SSH key into the backend container (e.g. `~/.ssh/id_ed25519:/app/ssh/id_ed25519:ro`).
3. Run:

```bash
docker compose up -d
```

The backend will auto-apply migrations on startup.

## Required Environment Variables
- `DATABASE_URL_SYNC`: sync SQLAlchemy connection string.
- `SSH_KEY_PATH`: absolute path to the SSH key inside the container.
- `SSH_USER`: default SSH user for host operations.
- `OFFLINE_MODE`: `true` to cache CAC content locally.

## Validate Installation
- API: `http://localhost:8000/docs`
- UI: `http://localhost:3000`
