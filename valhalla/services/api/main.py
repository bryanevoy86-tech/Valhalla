
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
    # Compute repo root relative to this file and add services/api to sys.path
    this_file = Path(__file__).resolve()
    repo_root = this_file.parents[3]  # .../valhalla/valhalla/services/api/main.py -> repo root
    services_api_dir = repo_root / "services" / "api"
    if services_api_dir.exists():
        sys.path.insert(0, str(services_api_dir))
except Exception as _e:
    # Non-fatal if path math fails
    print(f"INFO: services/api path not added: {_e}")

try:
    from app.core.config import settings
    from app.routers.health import router as health_router
    from app.routers.metrics import router as metrics_router
    from app.routers.capital import router as capital_router
    # Attempt to import builder router (optional)
    try:
        from app.routers.builder import router as builder_router
        BUILDER_AVAILABLE = True
    except Exception as e:
        print(f"WARNING: Could not import builder router (app.*): {e}")
        BUILDER_AVAILABLE = False
        builder_router = None
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
    except Exception as e:
        print(f"WARNING: Could not import builder router (valhalla.*): {e}")
        BUILDER_AVAILABLE = False
        builder_router = None


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
if 'BUILDER_AVAILABLE' in globals() and BUILDER_AVAILABLE and builder_router is not None:
    app.include_router(builder_router, prefix="/api")
else:
    print("WARNING: Builder router not registered (unavailable)")


@app.get("/")
def root():
    return {"service": "valhalla-api", "version": "3.4"}


# Test-client compatibility health endpoint
@app.get("/api/health")
def api_health():
    return {"ok": True, "app": "Valhalla API", "version": "3.4"}


@app.get("/debug/routes")
def debug_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({"path": route.path, "methods": list(route.methods)})
    return {
        "builder_available": bool('BUILDER_AVAILABLE' in globals() and BUILDER_AVAILABLE),
        "total_routes": len(app.routes),
        "routes": routes,
    }

# NOTE: Render uses: uvicorn main:app --host 0.0.0.0 --port $PORT

