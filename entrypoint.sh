#!/bin/sh
# Entrypoint script - Render cannot override this with dashboard settings
set -e

echo "==> Valhalla API Entrypoint"
echo "==> Working directory: $(pwd)"
echo "==> Python version: $(python --version)"
echo "==> Running migrations..."

cd /app/services/api

# Temporarily disable migrations due to schema state mismatch
# TODO: Fix duplicate table creation issues and make migrations idempotent
# alembic upgrade heads

echo "==> [MIGRATIONS DISABLED] - Schema state mismatch detected"
echo "==> Starting API with wrapper script..."
exec python start.py
