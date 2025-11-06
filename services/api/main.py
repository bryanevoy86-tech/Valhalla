import os
import sys

# PYTHONPATH is set to /app/services/api in Dockerfile, so app.* imports work directly
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.telemetry.middleware import TelemetryExceptionMiddleware
from app.metrics.middleware import MetricsMiddleware

from app.core.settings import settings

# Core routers (should always be available)
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.routers.capital import router as capital_router
from app.routers.telemetry import router as telemetry_router
from app.routers.admin import router as admin_router
from app.routers.ui_dashboard import router as ui_dashboard_router
from app.routers.system_health import router as system_health_router
from app.routers.analytics import router as analytics_router
from app.routers.alerts import router as alerts_router
from app.routers.roles import router as roles_router

# Pack routers with error handling
GRANTS_AVAILABLE = False
BUYERS_AVAILABLE = False
DEALS_AVAILABLE = False
MATCH_AVAILABLE = False
CONTRACTS_AVAILABLE = False
INTAKE_AVAILABLE = False
NOTIFY_AVAILABLE = False

try:
    from app.routers.grants import router as grants_router
    GRANTS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import grants router: {e}")
    grants_router = None

try:
    from app.routers.buyers import router as buyers_router
    BUYERS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import buyers router: {e}")
    buyers_router = None

try:
    from app.routers.deals import router as deals_router
    DEALS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import deals router: {e}")
    deals_router = None

try:
    from app.routers.match import router as match_router
    MATCH_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import match router: {e}")
    match_router = None

try:
    from app.routers.contracts import router as contracts_router
    CONTRACTS_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import contracts router: {e}")
    contracts_router = None

try:
    from app.routers.intake import router as intake_router
    INTAKE_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import intake router: {e}")
    intake_router = None

try:
    from app.routers.notify import router as notify_router
    NOTIFY_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import notify router: {e}")
    notify_router = None

# Try importing builder router with error handling
try:
    from app.routers.builder import router as builder_router
    BUILDER_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import builder router: {e}")
    BUILDER_AVAILABLE = False
    builder_router = None

# Try importing reports router (will be created by builder)
try:
    from app.routers.reports import router as reports_router
    REPORTS_AVAILABLE = True
except Exception as e:
    print(f"INFO: Reports router not yet available: {e}")
    REPORTS_AVAILABLE = False
    reports_router = None

# Try importing research and playbooks routers
try:
    from app.routers.research import router as research_router
    from app.routers.playbooks import router as playbooks_router
    from app.routers.jobs import router as jobs_router
    from app.routers.research_semantic import router as research_semantic_router
    RESEARCH_AVAILABLE = True
    RESEARCH_ERROR = None
except Exception as e:
    import traceback
    RESEARCH_ERROR = f"{str(e)}\n{traceback.format_exc()}"
    print(f"WARNING: Research/Playbooks/Jobs routers not available: {e}")
    print(f"Full traceback: {traceback.format_exc()}")
    RESEARCH_AVAILABLE = False
    research_router = None
    playbooks_router = None
    jobs_router = None
    research_semantic_router = None


app = FastAPI(title="Valhalla API", version="3.4")

# Auto-create tables on startup (dev-friendly; safe if tables already exist)
try:
    from app.core.db import Base, engine
    @app.on_event("startup")
    def startup_create_tables():
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e:
            print(f"WARNING: Failed to auto-create tables on startup: {e}")
except Exception as e:
    print(f"INFO: Skipping auto-create tables setup: {e}")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ALLOWED_ORIGINS", []),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-API-Key"],
)

# Global exception telemetry (best-effort)
try:
    app.add_middleware(TelemetryExceptionMiddleware)
except Exception as _e:  # pragma: no cover
    print(f"INFO: TelemetryExceptionMiddleware not enabled: {_e}")

# Runtime metrics collection (best-effort)
try:
    app.add_middleware(MetricsMiddleware)
except Exception as _e:  # pragma: no cover
    print(f"INFO: MetricsMiddleware not enabled: {_e}")

# Register routers (core routers always available)
app.include_router(health_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(capital_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(ui_dashboard_router, prefix="/api")
app.include_router(system_health_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(roles_router, prefix="/api")
app.include_router(alerts_router, prefix="/api")

# Security router (Pack 17) — optional import to avoid startup failure if deps missing
try:
    from app.routers.security import router as security_router
    SECURITY_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import security router: {e}")
    SECURITY_AVAILABLE = False
    security_router = None

if SECURITY_AVAILABLE and "security_router" in globals() and security_router is not None:
    app.include_router(security_router, prefix="/api")
else:
    print("INFO: Security router not registered")

# Encryption router (Pack 18) — optional import
try:
    from app.routers.encryption import router as encryption_router
    ENCRYPTION_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import encryption router: {e}")
    ENCRYPTION_AVAILABLE = False
    encryption_router = None

if ENCRYPTION_AVAILABLE and "encryption_router" in globals() and encryption_router is not None:
    app.include_router(encryption_router, prefix="/api")
else:
    print("INFO: Encryption router not registered")

# Logging router (Pack 19) — optional import
try:
    from app.routers.logging import router as logging_router
    LOGGING_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import logging router: {e}")
    LOGGING_AVAILABLE = False
    logging_router = None

if LOGGING_AVAILABLE and "logging_router" in globals() and logging_router is not None:
    app.include_router(logging_router, prefix="/api")
else:
    print("INFO: Logging router not registered")

# Pack routers (with availability checks)
if GRANTS_AVAILABLE and "grants_router" in globals() and grants_router is not None:
    app.include_router(grants_router, prefix="/api")
else:
    print("WARNING: Grants router not registered")

if BUYERS_AVAILABLE and "buyers_router" in globals() and buyers_router is not None:
    app.include_router(buyers_router, prefix="/api")
else:
    print("WARNING: Buyers router not registered")

if DEALS_AVAILABLE and "deals_router" in globals() and deals_router is not None:
    app.include_router(deals_router, prefix="/api")
else:
    print("WARNING: Deals router not registered")

if MATCH_AVAILABLE and "match_router" in globals() and match_router is not None:
    app.include_router(match_router, prefix="/api")
else:
    print("WARNING: Match router not registered")

if CONTRACTS_AVAILABLE and "contracts_router" in globals() and contracts_router is not None:
    app.include_router(contracts_router, prefix="/api")
else:
    print("WARNING: Contracts router not registered")

if INTAKE_AVAILABLE and "intake_router" in globals() and intake_router is not None:
    app.include_router(intake_router, prefix="/api")
else:
    print("WARNING: Intake router not registered")

if NOTIFY_AVAILABLE and "notify_router" in globals() and notify_router is not None:
    app.include_router(notify_router, prefix="/api")
else:
    print("WARNING: Notify router not registered")

if BUILDER_AVAILABLE and "builder_router" in globals() and builder_router is not None:
    app.include_router(builder_router, prefix="/api")
else:
    print("WARNING: Builder router not registered")
    
if REPORTS_AVAILABLE and "reports_router" in globals() and reports_router is not None:
    app.include_router(reports_router, prefix="/api")
else:
    print("INFO: Reports router not registered (will be available after builder creates it)")
    
if RESEARCH_AVAILABLE:
    if "research_router" in globals() and research_router is not None:
        app.include_router(research_router, prefix="/api")
    if "playbooks_router" in globals() and playbooks_router is not None:
        app.include_router(playbooks_router, prefix="/api")
    if "jobs_router" in globals() and jobs_router is not None:
        app.include_router(jobs_router, prefix="/api")
    if "research_semantic_router" in globals() and research_semantic_router is not None:
        app.include_router(research_semantic_router, prefix="/api")
else:
    print("INFO: Research/Playbooks/Jobs routers not registered")


@app.get("/")
def root():
    return {"service": "valhalla-api", "version": "3.4"}


@app.get("/debug/routes")
def debug_routes():
    """Debug endpoint to see registered routes and router availability"""
    routes = []
    from fastapi.routing import APIRoute
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append({"path": route.path, "methods": list(route.methods)})
    return {
        "grants_available": GRANTS_AVAILABLE,
        "buyers_available": BUYERS_AVAILABLE,
        "deals_available": DEALS_AVAILABLE,
        "match_available": MATCH_AVAILABLE,
        "contracts_available": CONTRACTS_AVAILABLE,
        "intake_available": INTAKE_AVAILABLE,
        "notify_available": NOTIFY_AVAILABLE,
        "builder_available": BUILDER_AVAILABLE,
        "reports_available": REPORTS_AVAILABLE,
        "research_available": RESEARCH_AVAILABLE,
        "research_error": RESEARCH_ERROR if 'RESEARCH_ERROR' in globals() else None,
        "total_routes": len(app.routes),
        "routes": routes
    }


# Compatibility health endpoint for tests/runtime expecting /api/health
@app.get("/api/health")
def health():
    return {"ok": True, "app": "Valhalla Backend", "version": "3.4"}

# NOTE: Render uses: uvicorn main:app --host 0.0.0.0 --port $PORT
