#!/bin/sh
set -e

echo "==> Valhalla API Entrypoint"
echo "==> Working directory: $(pwd)"
echo "==> Python version: $(python --version)"

cd /app/services/api

# Run database migrations with fallback for multiple heads
echo "==> Running database migrations..."
python run_migrations.py
MIGRATION_EXIT=$?

if [ $MIGRATION_EXIT -ne 0 ]; then
    echo "==> Migration failed with code $MIGRATION_EXIT"
    exit $MIGRATION_EXIT
fi

# Start FastAPI application
echo "==> Starting FastAPI application..."
exec python start.py
