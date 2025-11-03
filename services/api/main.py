import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.routers.capital import router as capital_router
from app.routers.telemetry import router as telemetry_router
from app.routers.grants import router as grants_router
from app.routers.buyers import router as buyers_router
from app.routers.deals import router as deals_router
from app.routers.match import router as match_router
from app.routers.contracts import router as contracts_router
from app.routers.intake import router as intake_router
from app.routers.notify import router as notify_router
from app.routers.admin import router as admin_router

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

# Routers
app.include_router(health_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(capital_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(grants_router, prefix="/api")
app.include_router(buyers_router, prefix="/api")
app.include_router(deals_router, prefix="/api")
app.include_router(match_router, prefix="/api")
app.include_router(contracts_router, prefix="/api")
app.include_router(intake_router, prefix="/api")
app.include_router(notify_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
if BUILDER_AVAILABLE:
    app.include_router(builder_router, prefix="/api")
else:
    print("WARNING: Builder router not registered due to import error")
if REPORTS_AVAILABLE:
    app.include_router(reports_router, prefix="/api")
else:
    print("INFO: Reports router not registered (will be available after builder creates it)")
if RESEARCH_AVAILABLE:
    app.include_router(research_router, prefix="/api")
    app.include_router(playbooks_router, prefix="/api")
    app.include_router(jobs_router, prefix="/api")
    app.include_router(research_semantic_router, prefix="/api")
else:
    print("INFO: Research/Playbooks/Jobs routers not registered")


@app.get("/")
def root():
    return {"service": "valhalla-api", "version": "3.4"}


@app.get("/debug/routes")
def debug_routes():
    """Debug endpoint to see registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({"path": route.path, "methods": list(route.methods)})
    return {
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
