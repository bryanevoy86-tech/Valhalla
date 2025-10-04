FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Healthcheck endpoint assumed at /healthz
EXPOSE 10000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "valhalla.services.api.main:app", "-b", "0.0.0.0:10000", "-w", "2", "--timeout", "120"]
