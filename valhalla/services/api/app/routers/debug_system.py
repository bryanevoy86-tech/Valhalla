# services/api/app/routers/debug_system.py

"""
System introspection router for PACK S.
Provides /debug endpoints for route listing and system health checking.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.system_introspection import list_routes, system_snapshot
from app.schemas.system_debug import DebugRoutesResponse, SystemSnapshot

router = APIRouter(prefix="/debug", tags=["Debug", "System"])


@router.get("/routes", response_model=DebugRoutesResponse, summary="List all registered routes")
def debug_routes(request: Request):
    """
    List all routes registered in the FastAPI application.
    Useful for verifying that all packs are properly integrated.
    """
    app = request.app
    routes = list_routes(app)
    return {
        "routes": routes,
        "count": len(app.routes),
    }


@router.get("/system", response_model=SystemSnapshot, summary="Get system health snapshot")
def debug_system(request: Request, db: Session = Depends(get_db)):
    """
    Get a comprehensive snapshot of system health including:
    - Total registered routes
    - Database connectivity
    - Subsystem table availability (professionals, contracts, documents, tasks, audit, governance)
    
    This is read-only and provides rapid health status for monitoring.
    """
    app = request.app
    snapshot = system_snapshot(app, db)
    return snapshot
