
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Try the runtime layout used when running from services/api (Render):
# `from app...`. If tests import the package as `valhalla.services.api`,
# fall back to the in-repo full package path.
"""Ensure both import layouts work (package and runtime dirs).

We prefer importing via `app.*` which maps to services/api/app/* when running
the API directly. In some environments (tests, package imports), the module
layout is `valhalla.services.api.app.*`. To make `app.*` available even when
this file is imported as part of the valhalla package, we add the sibling
services/api directory to sys.path if it exists.
"""
try:
    # Add the correct services/api directory to sys.path so `import app.*` works.
    # We search upwards for a folder that contains services/api/app
    this_file = Path(__file__).resolve()
    added_path = None
    for parent in list(this_file.parents)[:6]:
        candidate = parent / "services" / "api"
        if (candidate / "app").exists():
            sys.path.insert(0, str(candidate))
            added_path = candidate
            break
    if not added_path:
        print("INFO: Could not locate services/api path to add to sys.path")
    else:
        print(f"INFO: Added to sys.path: {added_path}")
except Exception as _e:
    # Non-fatal if path math fails
    print(f"INFO: services/api path not added: {_e}")

try:
    from app.core.config import settings
    from app.routers.health import router as health_router
    from app.routers.metrics import router as metrics_router
    from app.routers.capital import router as capital_router
    from app.routers.admin import router as admin_router
    # Attempt to import builder router (optional)
    try:
        from app.routers.builder import router as builder_router
        BUILDER_AVAILABLE = True
        BUILDER_ERROR = None
    except Exception as e:
        BUILDER_ERROR = str(e)
        print(f"WARNING: Could not import builder router (app.*): {e}")
        BUILDER_AVAILABLE = False
        builder_router = None
    # Attempt to import reports router (optional, created by builder)
    try:
        from app.routers.reports import router as reports_router
        REPORTS_AVAILABLE = True
    except Exception as e:
        print(f"INFO: Reports router not yet available (app.*): {e}")
        REPORTS_AVAILABLE = False
        reports_router = None
    # Attempt to import research and playbooks routers
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
        print(f"WARNING: Research/Playbooks/Jobs routers not available (app.*): {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        RESEARCH_AVAILABLE = False
        research_router = None
        playbooks_router = None
        jobs_router = None
        research_semantic_router = None
except Exception:
    # fallback for test runner import path
    from valhalla.services.api.app.core.config import settings
    from valhalla.services.api.app.routers.health import router as health_router
    from valhalla.services.api.app.routers.metrics import router as metrics_router
    from valhalla.services.api.app.routers.capital import router as capital_router
    # Fallback import for builder
    try:
        from valhalla.services.api.app.routers.builder import router as builder_router
        BUILDER_AVAILABLE = True
        BUILDER_ERROR = None
    except Exception as e:
        BUILDER_ERROR = str(e)
        print(f"WARNING: Could not import builder router (valhalla.*): {e}")
        BUILDER_AVAILABLE = False
        builder_router = None
    # Fallback import for reports
    try:
        from valhalla.services.api.app.routers.reports import router as reports_router
        REPORTS_AVAILABLE = True
    except Exception as e:
        print(f"INFO: Reports router not yet available (valhalla.*): {e}")
        REPORTS_AVAILABLE = False
        reports_router = None
    # Fallback import for research and playbooks
    try:
        from valhalla.services.api.app.routers.research import router as research_router
        from valhalla.services.api.app.routers.playbooks import router as playbooks_router
        from valhalla.services.api.app.routers.jobs import router as jobs_router
        from valhalla.services.api.app.routers.research_semantic import router as research_semantic_router
        RESEARCH_AVAILABLE = True
        RESEARCH_ERROR = None
    except Exception as e:
        import traceback
        RESEARCH_ERROR = f"{str(e)}\n{traceback.format_exc()}"
        print(f"WARNING: Research/Playbooks/Jobs routers not available (valhalla.*): {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        RESEARCH_AVAILABLE = False
        research_router = None
        playbooks_router = None
        jobs_router = None
        research_semantic_router = None


app = FastAPI(title="Valhalla API", version="3.4")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "X-API-Key"],
)

# Routers (mounted under /api)
app.include_router(health_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(capital_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
if 'BUILDER_AVAILABLE' in globals() and BUILDER_AVAILABLE and builder_router is not None:
    app.include_router(builder_router, prefix="/api")
else:
    print("WARNING: Builder router not registered (unavailable)")
if 'REPORTS_AVAILABLE' in globals() and REPORTS_AVAILABLE and reports_router is not None:
    app.include_router(reports_router, prefix="/api")
else:
    print("INFO: Reports router not registered (will be available after builder creates it)")
if 'RESEARCH_AVAILABLE' in globals() and RESEARCH_AVAILABLE and research_router is not None:
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
        "builder_error": BUILDER_ERROR,
        "reports_available": REPORTS_AVAILABLE if 'REPORTS_AVAILABLE' in globals() else False,
        "research_available": RESEARCH_AVAILABLE if 'RESEARCH_AVAILABLE' in globals() else False,
        "research_error": RESEARCH_ERROR if 'RESEARCH_ERROR' in globals() else None,
        "total_routes": len(app.routes),
        "routes": routes
    }


# Test-client compatibility health endpoint
@app.get("/api/health")
def api_health():
    return {"ok": True, "app": "Valhalla API", "version": "3.4"}


@app.get("/debug/status")
def debug_status():
    """Detailed status endpoint showing import errors"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({"path": route.path, "methods": list(route.methods)})
    return {
        "builder_available": bool('BUILDER_AVAILABLE' in globals() and BUILDER_AVAILABLE),
        "builder_error": globals().get('BUILDER_ERROR'),
        "reports_available": bool('REPORTS_AVAILABLE' in globals() and globals().get('REPORTS_AVAILABLE')),
        "research_available": bool('RESEARCH_AVAILABLE' in globals() and globals().get('RESEARCH_AVAILABLE')),
        "research_error": globals().get('RESEARCH_ERROR'),
        "total_routes": len(app.routes),
        "routes": routes,
    }

# NOTE: Render uses: uvicorn main:app --host 0.0.0.0 --port $PORT

