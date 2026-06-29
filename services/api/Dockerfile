FROM python:3.11-slim

# Cache bust: 2026-06-28 22:58 - Force rebuild with latest start.py and alembic changes
#ARG CACHE_BUST_TIME

# Copy only necessary files to /app
WORKDIR /app
COPY . /app

# Install requirements
RUN pip install --no-cache-dir -r /app/services/api/requirements.txt

# Set working directory and PYTHONPATH
WORKDIR /app/services/api
ENV PYTHONPATH=/app/services/api

EXPOSE 8000

# Default command (overridden by render.yaml)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
