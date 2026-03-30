#!/bin/sh
set -e

echo "==> Valhalla API Entrypoint"
echo "==> Working directory: $(pwd)"
echo "==> Python version: $(python --version)"

cd /app/services/api

# Migrations now handled by start.py with proper fail-loud error handling
echo "==> Starting API (migrations handled by start.py)..."
exec python start.py
