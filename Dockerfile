FROM python:3.11-slim

# BUILD CACHE INVALIDATION: 2026-04-19T02:50:00Z
# Forcing Render redeploy - latest commits from main branch
# If you see this timestamp, the rebuild worked correctly.

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

# Explicitly ensure alembic folder and config are copied to root for migrations
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

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
