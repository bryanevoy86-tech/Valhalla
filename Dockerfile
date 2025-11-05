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
ENV PYTHONPATH=/app/services/api

# Change to services/api directory and run from there
WORKDIR /app/services/api

# Run migrations then start the API
CMD echo "PWD: $(pwd)" && \
    echo "PYTHONPATH: $PYTHONPATH" && \
    echo "Python version:" && python --version && \
    echo "Running migrations..." && \
    alembic upgrade head && \
    echo "Starting uvicorn..." && \
    exec python -c "import sys; sys.path.insert(0, '/app/services/api'); from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=${PORT:-10000})"
