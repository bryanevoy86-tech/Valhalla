# services/api/app/routers/ui_map.py

"""
UI Map Router for PACK U: Frontend Preparation
Provides a structured, curated map of API modules and endpoints for frontend UI generation.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.services.ui_map import get_ui_map

router = APIRouter(prefix="/ui-map", tags=["Frontend", "UI"])


@router.get("/", summary="Get UI navigation map")
def read_ui_map():
    """
    Returns a curated, structured map of API modules, sections, and endpoints.
    
    This map is designed for frontend (WeWeb) to auto-generate:
    - Navigation menus
    - UI screens
    - Form layouts
    - Data models
    
    For a complete, unfiltered list of all routes, use /debug/routes instead.
    
    Response includes:
    - Logical module groupings
    - Section organization within modules
    - Endpoint details (method, path, summary)
    - Metadata for versioning
    """
    return get_ui_map()
