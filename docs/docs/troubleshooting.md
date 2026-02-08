---
title: Troubleshooting
---

# Troubleshooting

## CAC Fetch Fails
- Check network access to GitHub.
- Verify `OFFLINE_MODE` and cache path.
- Ensure Docker has outbound access.

## SSH Connection Errors
- Confirm the SSH key is mounted and readable.
- Verify the target host allows key-based auth.
- Test with `ssh -i key user@host`.

## DB Migration Failures
- Ensure Postgres is reachable.
- Confirm `DATABASE_URL_SYNC` is correct.
- Restart backend after DB health is restored.
