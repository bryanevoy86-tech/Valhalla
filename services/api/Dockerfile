FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the entire repository
COPY . /app

# Install API service requirements  
# Handle both local (./services/api) and Render (./valhalla/services/api) paths
RUN if [ -f services/api/requirements.txt ]; then \
        pip install --no-cache-dir -r services/api/requirements.txt; \
    elif [ -f valhalla/services/api/requirements.txt ]; then \
        pip install --no-cache-dir -r valhalla/services/api/requirements.txt; \
    else \
        echo "ERROR: Cannot find requirements.txt" && exit 1; \
    fi

# Expose API port
EXPOSE 8000

# Set Python path and working directory
# Handle both local and Render directory structures
RUN if [ -d services/api ]; then \
        echo "Local structure detected"; \
    elif [ -d valhalla/services/api ]; then \
        echo "Render structure detected" && \
        ln -s valhalla/services services || true; \
    fi

ENV PYTHONPATH=/app/services/api

# Run the FastAPI app
WORKDIR /app/services/api
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
