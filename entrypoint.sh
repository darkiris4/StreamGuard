#!/usr/bin/env sh
set -eu

echo "Running database migrations..."
for i in 1 2 3 4 5 6 7 8 9 10; do
  if alembic -c /app/alembic.ini upgrade head; then
    break
  fi
  echo "Migration attempt $i failed, retrying in 2s..."
  sleep 2
done

echo "Starting API server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
