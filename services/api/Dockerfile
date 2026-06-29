FROM python:3.11-slim

# Build-time environment to force fresh builds
ENV FORCE_BUILD_2026_06_28_LATE_EVENING=true

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
