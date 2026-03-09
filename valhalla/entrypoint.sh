#!/bin/sh
set -e

echo "==> Valhalla API Entrypoint"
echo "==> Working directory: $(pwd)"
echo "==> Python version: $(python --version)"

cd /app/services/api

if [ "${SKIP_MIGRATIONS:-0}" = "1" ]; then
  echo "==> SKIP_MIGRATIONS=1, skipping alembic upgrade"
else
  echo "==> Running migrations (single head)..."
  alembic upgrade head
fi

echo "==> Starting API..."
exec python start.py
