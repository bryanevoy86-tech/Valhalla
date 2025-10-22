
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Try the runtime layout used when running from services/api (Render):
# `from app...`. If tests import the package as `valhalla.services.api`,
# fall back to the in-repo full package path.
try:
    from app.core.config import settings
    from app.routers.health import router as health_router
    from app.routers.metrics import router as metrics_router
    from app.routers.capital import router as capital_router
except Exception:
    # fallback for test runner import path
    from valhalla.services.api.app.core.config import settings
    from valhalla.services.api.app.routers.health import router as health_router
    from valhalla.services.api.app.routers.metrics import router as metrics_router
    from valhalla.services.api.app.routers.capital import router as capital_router


app = FastAPI(title="Valhalla API", version="3.4")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# Routers (mounted under /api)
app.include_router(health_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(capital_router, prefix="/api")


@app.get("/")
def root():
    return {"service": "valhalla-api", "version": "3.4"}


# Test-client compatibility health endpoint
@app.get("/api/health")
def api_health():
    return {"ok": True, "app": "Valhalla API", "version": "3.4"}

# NOTE: Render uses: uvicorn main:app --host 0.0.0.0 --port $PORT

