FROM python:3.11-slim

# system deps (psycopg2 build, if needed in future)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl netcat-traditional \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# install deps first for better docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app code
COPY app ./app

# default cmd
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
