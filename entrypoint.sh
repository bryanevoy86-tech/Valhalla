#!/bin/sh
# Entrypoint script - Render cannot override this with dashboard settings
set -e

echo "==> Valhalla API Entrypoint"
echo "==> Working directory: $(pwd)"
echo "==> Python version: $(python --version)"
echo "==> Running migrations..."

cd /app/services/api
alembic upgrade heads

echo "==> Starting API with wrapper script..."
exec python start.py
