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

# Set working directory to where main.py is located
WORKDIR /app/services/api

# Run uvicorn (Render sets PORT env var to 10000)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
