FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Healthcheck endpoint assumed at /healthz
EXPOSE 10000
 CMD /bin/sh -c "python -m uvicorn valhalla.services.api.main:app --host 0.0.0.0 --port ${PORT}"
