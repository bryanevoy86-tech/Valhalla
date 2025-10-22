import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings
from app.routers.health import router as health_router
from app.routers.metrics import router as metrics_router
from app.routers.capital import router as capital_router

# Try importing builder router with error handling
try:
    from app.routers.builder import router as builder_router
    BUILDER_AVAILABLE = True
except Exception as e:
    print(f"WARNING: Could not import builder router: {e}")
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

# Routers
app.include_router(health_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(capital_router, prefix="/api")
if BUILDER_AVAILABLE:
    app.include_router(builder_router, prefix="/api")
else:
    print("WARNING: Builder router not registered due to import error")


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
        "total_routes": len(app.routes),
        "routes": routes
    }


# Compatibility health endpoint for tests/runtime expecting /api/health
@app.get("/api/health")
def health():
    return {"ok": True, "app": "Valhalla Backend", "version": "3.4"}

# NOTE: Render uses: uvicorn main:app --host 0.0.0.0 --port $PORT
