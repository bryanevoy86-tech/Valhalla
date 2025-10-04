FROM python:3.11-slim

# git for auto-commit support
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# allow git operations inside container on mounted repo
RUN git config --global --add safe.directory /app

COPY . .
ENV PYTHONUNBUFFERED=1
