FROM python:3.11-slim

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
# Make both the repo root (/app) and the API service dir importable
ENV PYTHONPATH=/app:/app/services/api

# Debug and run (works whether start command is overridden or not)
CMD echo "PWD: $(pwd)" && \
    echo "PYTHONPATH: $PYTHONPATH" && \
    echo "Listing /app and /app/services/api:" && \
    ls -la /app || true && \
    ls -la /app/services/api || true && \
    echo "Starting uvicorn (valhalla.services.api.main:app) on port ${PORT:-10000}..." && \
    python -m uvicorn valhalla.services.api.main:app --host 0.0.0.0 --port ${PORT:-10000}
