FROM python:3.11-slim

# BUILD CACHE INVALIDATION: 2026-06-28T00:37:00Z
# Forcing clean rebuild - explicitly copying from services/api/alembic
# Using services/api as source since root alembic not appearing in Docker context

# git for auto-commit support
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY services/api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# allow git operations inside container on mounted repo
RUN git config --global --add safe.directory /app

# Copy entire repository
COPY . .

# Copy alembic from services/api to root (authoritative source)
COPY services/api/alembic /app/alembic
COPY services/api/alembic.ini /app/alembic.ini

# Verify alembic files are present for migrations
RUN test -d /app/alembic && test -f /app/alembic.ini && echo "✓ Alembic files present" || (echo "✗ Alembic files missing" && exit 1)

# Copy and set executable permissions for entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/services/api

# Change to services/api directory and run from there
WORKDIR /app/services/api

# Use entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
