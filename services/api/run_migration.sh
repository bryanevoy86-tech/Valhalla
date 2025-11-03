#!/bin/bash
# Migration script for Render deployment
# Run this via Render shell or as a build command

set -e

echo "Running Alembic migrations..."
cd /opt/render/project/src/services/api
alembic upgrade head

echo "Migrations complete!"
