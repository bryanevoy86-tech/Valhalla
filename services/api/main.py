from __future__ import annotations

import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.policy.router import router as policy_router
from app.security.auth import router as ops_router  # owner auth (+ /ops/token)
from app.routers.engine_admin import router as engine_admin_router
from app.routers.outcomes import router as outcomes_router
from app.routers.intake import router as intake_router
from app.routers.intake_admin import router as intake_admin_router
from app.routers.metrics import router as metrics_router
from app.routers.runbook_status import router as runbook_status_router


def _truthy(v: str | None, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


APP_ENV = (os.getenv("APP_ENV") or "dev").strip().lower()
PUBLIC_DOCS = _truthy(os.getenv("VALHALLA_PUBLIC_DOCS"), False)

docs_url = "/docs"
openapi_url = "/openapi.json"
redoc_url = "/redoc"

# Security hardening: disable docs in production unless explicitly enabled
if APP_ENV == "production" and not PUBLIC_DOCS:
    docs_url = None
    openapi_url = None
    redoc_url = None


app = FastAPI(
    title="Valhalla API",
    version="0.1.0",
    docs_url=docs_url,
    openapi_url=openapi_url,
    redoc_url=redoc_url,
)

# CORS (locked minimal: env-driven)
cors = (os.getenv("CORS_ALLOWED_ORIGINS") or "").strip()
if cors:
    allow_origins = [o.strip() for o in cors.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
    )

# Routers
app.include_router(policy_router)
app.include_router(ops_router)  # /ops/* guarded endpoints
app.include_router(engine_admin_router)  # /api/engines/* (Heimdall-governed)
app.include_router(outcomes_router)  # /api/outcomes (closed-loop learning)
app.include_router(intake_router)  # /api/intake (quarantine-first)
app.include_router(intake_admin_router)  # /api/intake/admin (promotion)
app.include_router(metrics_router)  # /api/metrics (gate inputs)
app.include_router(runbook_status_router)  # /api/runbook/status (unified health)


@app.api_route("/", methods=["GET", "HEAD"])
def root(_: Response):
    return {"ok": True, "service": "valhalla-api"}


@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/healthz", summary="Health check alias")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(404)
def not_found(_, __):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
