import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.routers.capital import router as capital_router
from app.routers.builder import router as builder_router


app = FastAPI(title="Valhalla API", version="3.4")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Routers
app.include_router(health_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(capital_router, prefix="/api")
app.include_router(builder_router, prefix="/api")


@app.get("/")
def root():
    return {"service": "valhalla-api", "version": "3.4"}


# Compatibility health endpoint for tests/runtime expecting /api/health
@app.get("/api/health")
def health():
    return {"ok": True, "app": "Valhalla Backend", "version": "3.4"}

# NOTE: Render uses: uvicorn main:app --host 0.0.0.0 --port $PORT
