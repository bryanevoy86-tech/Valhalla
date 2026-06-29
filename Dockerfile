FROM python:3.11-slim

# BUILD CACHE INVALIDATION: 2026-06-29T00:45:00Z
# Canonical single alembic at root, direct CMD (no entrypoint)

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

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/services/api

# Change to services/api directory for execution
WORKDIR /app/services/api

# Use direct command - start.py handles migrations and startup
# If alembic files missing, start.py will fail with clear error
CMD ["python", "start.py"]
