FROM python:3.11-slim

# Copy the entire repository to /app
WORKDIR /app
COPY . /app

# Install requirements - check both possible locations
RUN if [ -f /app/services/api/requirements.txt ]; then \
        echo "Installing from /app/services/api/requirements.txt" && \
        pip install --no-cache-dir -r /app/services/api/requirements.txt; \
    elif [ -f /app/valhalla/services/api/requirements.txt ]; then \
        echo "Installing from /app/valhalla/services/api/requirements.txt" && \
        pip install --no-cache-dir -r /app/valhalla/services/api/requirements.txt; \
    else \
        echo "ERROR: Cannot find requirements.txt" && ls -la /app && exit 1; \
    fi

# Create a startup script that handles both directory structures
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'if [ -d /app/services/api ]; then' >> /start.sh && \
    echo '  echo "Using /app/services/api"' >> /start.sh && \
    echo '  cd /app/services/api' >> /start.sh && \
    echo '  export PYTHONPATH=/app/services/api' >> /start.sh && \
    echo 'elif [ -d /app/valhalla/services/api ]; then' >> /start.sh && \
    echo '  echo "Using /app/valhalla/services/api"' >> /start.sh && \
    echo '  cd /app/valhalla/services/api' >> /start.sh && \
    echo '  export PYTHONPATH=/app/valhalla/services/api' >> /start.sh && \
    echo 'else' >> /start.sh && \
    echo '  echo "ERROR: Cannot find services/api directory"' >> /start.sh && \
    echo '  ls -la /app' >> /start.sh && \
    echo '  exit 1' >> /start.sh && \
    echo 'fi' >> /start.sh && \
    echo 'echo "PYTHONPATH=$PYTHONPATH"' >> /start.sh && \
    echo 'echo "PWD=$(pwd)"' >> /start.sh && \
    echo 'echo "Starting uvicorn..."' >> /start.sh && \
    echo 'exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}' >> /start.sh && \
    chmod +x /start.sh

EXPOSE 8000

CMD ["/start.sh"]
