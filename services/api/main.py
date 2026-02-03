from __future__ import annotations

import os
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.policy.router import router as policy_router
from app.security.auth import router as ops_router  # owner auth (+ /ops/token)
from app.routers.admin_go_live import router as admin_go_live_router
from app.routers.engine_admin import router as engine_admin_router
from app.routers.outcomes import router as outcomes_router
from app.routers.intake import router as intake_router
from app.routers.intake_admin import router as intake_admin_router
from app.routers.metrics import router as metrics_router
from app.routers.runbook_status import router as runbook_status_router
from app.routers import runbook as governance_runbook_router
from app.routers import go_live as governance_go_live_router
from app.core.settings import settings


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

# CORS: Support WeWeb (editor/preview/app) + localhost dev + custom origins from env
ALLOWED_ORIGINS = [
    "https://editor.weweb.io",
    "https://app.weweb.io",
    "https://preview.weweb.io",
    "http://localhost:3000",      # Local WeWeb dev
    "http://localhost:5173",      # Local Vite/dev server
] + settings.cors_allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https:\/\/.*\.weweb\.io$|^https:\/\/.*\.weweb\.app$",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,  # Cache preflight for 24 hours
)

# Routers
# NOTE: Two runbook endpoints exist (kept for backward compatibility):
#   - /api/runbook/status (runbook_status_router): Legacy unified health
#   - /api/governance/runbook/status (governance_runbook_router): Canonical governance/blockers/policies
# RECOMMENDED: Use /api/governance/runbook/status for go-live monitoring + WeWeb health
# TODO: Consider deprecating /api/runbook/status after migration period

app.include_router(policy_router)
app.include_router(ops_router)  # /ops/* guarded endpoints
app.include_router(admin_go_live_router, prefix="/api")  # /api/admin/* go-live endpoints
app.include_router(engine_admin_router)  # /api/engines/* (Heimdall-governed)
app.include_router(outcomes_router)  # /api/outcomes (closed-loop learning)
app.include_router(intake_router)  # /api/intake (quarantine-first)
app.include_router(intake_admin_router)  # /api/intake/admin (promotion)
app.include_router(metrics_router)  # /api/metrics (gate inputs)
app.include_router(runbook_status_router)  # /api/runbook/status (legacy health)
app.include_router(governance_runbook_router.router, prefix="/api")  # /api/governance/runbook/status (canonical)
app.include_router(governance_go_live_router.router, prefix="/api")  # /api/governance/go-live/* (go-live control)

# --- Notification API (System Email) ---
from app.api.notify.test_email_router import router as notify_test_router
app.include_router(notify_test_router, prefix="/api")  # /api/notify/test-email

# --- Outbox & Jobs Routers (email/webhook dispatch) ---
try:
    from app.routers import notify
    app.include_router(notify.router, prefix="/api")  # /api/notify/email, /api/notify/webhook
    print("[main.py] Notify router registered")
except Exception as e:
    print(f"[main.py] Skipping notify router: {e}")

try:
    from app.routers import jobs
    app.include_router(jobs.router, prefix="/api")  # /api/jobs/notify/dispatch, etc
    print("[main.py] Jobs router registered")
except Exception as e:
    print(f"[main.py] Skipping jobs router: {e}")

# DEBUG: Route list endpoint (gated behind env var or X-API-Key header for security)
def _get_debug_routes():
    """Helper to list all routes (used by both __routes endpoints)."""
    return sorted({f"{r.methods if hasattr(r, 'methods') else '?'} {r.path}" 
                   for r in app.router.routes 
                   if hasattr(r, 'path')})

if os.getenv("EXPOSE_DEBUG_ROUTES") == "1":
    @app.get("/__routes", include_in_schema=False)
    def __routes():
        """Debug endpoint: list all registered routes (when EXPOSE_DEBUG_ROUTES=1)."""
        return JSONResponse(_get_debug_routes())
else:
    @app.get("/__routes", include_in_schema=False)
    def __routes_disabled():
        """Debug endpoint disabled (EXPOSE_DEBUG_ROUTES not set)."""
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")


@app.get("/debug/main-loaded", include_in_schema=False)
def debug_main_loaded():
    """Debug endpoint to verify which main.py is loaded."""
    return {"message": "services/api/main.py is loaded"}


@app.get("/debug/routes", include_in_schema=False)
def debug_routes():
    """List all registered routes (available in dev/staging for debugging)."""
    if APP_ENV == "production" and not os.getenv("EXPOSE_DEBUG_ROUTES"):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not available in production")
    return _get_debug_routes()


@app.api_route("/", methods=["GET", "HEAD"])
def root(_: Response):
    return {"ok": True, "service": "valhalla-api"}


@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/healthz", summary="Health check alias")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/governance", summary="Governance root hint")
def governance_root():
    """Root governance endpoint redirects to canonical status endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "hint": "Use /api/governance/runbook/status for full governance status",
            "status_endpoint": "/api/governance/runbook/status",
        },
    )


@app.exception_handler(404)
def not_found(_, __):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
