FROM python:3.11-slim

# Set working directory to repository root inside the image
WORKDIR /app

# Copy the entire repository (Docker ignore file should exclude large/unneeded files)
COPY . /app

# Install API service requirements
RUN pip install --no-cache-dir -r services/api/requirements.txt

# Expose API port
EXPOSE 8000

# Ensure Python can import from the API service package
ENV PYTHONPATH=/app/services/api

# Run the FastAPI app
WORKDIR /app/services/api
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
