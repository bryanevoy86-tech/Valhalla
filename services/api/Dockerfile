FROM python:3.11-slim
WORKDIR /app/valhalla/services/api/app
COPY ../../valhalla /app/valhalla
COPY ../../valhalla/services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
EXPOSE 8000
ENV PYTHONPATH=/app/valhalla/services/api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
