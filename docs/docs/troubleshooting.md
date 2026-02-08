---
title: Troubleshooting
---

# Troubleshooting

## CAC Content Fetch Fails

- **Check network access** — the backend container needs outbound HTTPS to `github.com` and `api.github.com`.
- **GitHub rate limiting** — unauthenticated API requests are limited to 60/hour.
  Set `GITHUB_TOKEN` in `docker-compose.yml` for 5000/hour, or switch to Offline mode.
- **Profile listing vs artifacts** — profile dropdowns are fetched live from GitHub.
  Artifacts (datastream XML, playbooks) are downloaded only when you run an audit/mitigate.
- **Offline mode** — toggle the switch in the toolbar or set `OFFLINE_MODE=true` in `docker-compose.yml`. This clones the full repo instead of using the API.
- **Cache fallback** — if a fetch fails, StreamGuard automatically uses whatever is already cached. If the cache is empty, you'll see an error.
- **Check logs** — `docker compose logs backend --tail=50` will show the actual error from the fetch attempt.

## SSH Connection Errors

- **Key not mounted** — ensure `docker-compose.yml` mounts `~/.ssh:/app/ssh:ro`. Check with `docker compose exec backend ls -la /app/ssh/`.
- **Wrong key permissions** — SSH keys must be readable. Inside the container they're mounted read-only, which is correct.
- **Host not in SSH config** — StreamGuard auto-loads hosts from `~/.ssh/config`.
  If a host isn't there, add it and click **Re-scan SSH Config** in the UI.
- **Test from the container** — `docker compose exec backend ssh -i /app/ssh/id_ed25519 root@target-host hostname`.
- **Paramiko errors** — the "Test" button on the Hosts page uses paramiko. If it fails but manual SSH works, check that the key type is supported (Ed25519, RSA).

## Audit Returns No Results

- **CAC content missing** — check `/api/cac/status` to verify content is cached for the distro.
- **Wrong distro** — use the specific product ID (`rhel9`, not `rhel`). The datastream file must match.
- **OpenSCAP not installed** — the backend Docker image includes `openscap-scanner`, but if running outside Docker, install it: `apt install openscap-scanner`.

## Mitigation Does Nothing

- **Dry-run is default** — the UI runs `ansible --check` by default. Use the API with `"dry_run": false` to apply actual changes.
- **Playbook not found** — check `/api/cac/status` to see if playbooks are cached for your distro/profile combination.
- **Ansible connectivity** — Ansible uses the same SSH key. If audit works but mitigate doesn't, check that `ansible` is installed in the container (it is by default).

## Database Migration Failures

- **Postgres not ready** — the backend depends on `db`, but Docker Compose doesn't wait for Postgres to accept connections. Restart the backend: `docker compose restart backend`.
- **Connection refused** — confirm `DATABASE_URL_SYNC` matches the Postgres service name (`db`), port (`5432`), and credentials.

## UI Can't Reach the API

- **Accessing from LAN** — the UI uses relative `/api` paths proxied through the Vite dev server. Access via `http://<server-ip>:3000`, not `localhost`.
- **Backend not running** — check `docker compose ps` and `docker compose logs backend`.
- **Port conflicts** — ensure ports 3000, 8000, and 5432 aren't used by other services.
