---
sidebar_position: 2
title: Setup
---

# Setup and Installation

## Prerequisites

| Requirement | Notes |
|---|---|
| Docker Engine + Docker Compose | v2+ recommended |
| SSH key pair | Ed25519 or RSA; must grant passwordless access to target hosts |
| Target hosts | RHEL 7/8/9, Fedora, Ubuntu 20.04/22.04/24.04, or Debian 11/12 |

## 1. Clone and Configure

```bash
git clone <repo-url> StreamGuard
cd StreamGuard
cp .env.example .env
```

Edit `.env` if you need to override defaults (database URL, SSH user, etc.). Most users can leave it as-is.

## 2. SSH Key Setup

StreamGuard mounts your entire `~/.ssh/` directory (read-only) into the backend
container. On startup it parses `~/.ssh/config` to auto-discover targets.

**Ensure your key works** from the StreamGuard server to every target:

```bash
ssh -i ~/.ssh/id_ed25519 root@target-host "hostname"
```

If that succeeds, StreamGuard can reach the host. No additional SSH
configuration inside the container is needed.

Hosts displayed in the UI map directly to `~/.ssh/config` fields:

- **Host** -> `Host`
- **HostName** -> `HostName`
- **User** -> `User`
- **Port** -> `Port`
- **IdentityFile** -> `IdentityFile`
- **ProxyJump** -> `ProxyJump`

## 3. Start the Stack

```bash
docker compose up -d
```

This brings up four services:

| Service | Port | Purpose |
|---|---|---|
| **frontend** | 3000 | Web UI (Vite dev server, proxies API calls to backend) |
| **backend** | 8000 | FastAPI — audit, mitigate, CAC fetch, host management |
| **db** | 5432 | PostgreSQL for scan results, jobs, hosts, profiles |
| **docs** | 3001 | Docusaurus user guide |

The backend automatically runs Alembic migrations on startup.

## 4. Validate

- **UI:** `http://<server-ip>:3000`
- **API docs:** `http://<server-ip>:8000/docs`
- **Health check:** `curl http://<server-ip>:8000/health`

The UI is accessible from any machine on the network — use the server's LAN IP, not `localhost`.

## Environment Variables

These are set in `docker-compose.yml` under the `backend` service:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | Async SQLAlchemy URL |
| `DATABASE_URL_SYNC` | PostgreSQL connection | Sync SQLAlchemy URL |
| `CAC_GITHUB_URL` | `https://github.com/ComplianceAsCode/content` | CAC repo URL |
| `OFFLINE_MODE` | `false` | Set `true` to use local git clone instead of GitHub releases |
| `SSH_KEY_PATH` | `/app/ssh/id_ed25519` | Default SSH key inside the container (auto-detected if present) |
| `GITHUB_TOKEN` | *(empty)* | Optional GitHub PAT for higher API rate limits (5000/hr) |
| `SSH_USER` | `root` | Default SSH user for host operations |
| `MAX_CONCURRENT_HOSTS` | `10` | Parallel scan/remediation limit |
| `CORS_ORIGINS` | `*` | Allowed origins (leave `*` for internal tools) |

## Updating

```bash
git pull
docker compose up -d --build
```

The backend will apply any new database migrations automatically.
