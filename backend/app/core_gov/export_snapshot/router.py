"""
P-EXPORTSNAP-1: Export snapshot API router.

GET /core/export_snapshot - Export system snapshot
"""
from fastapi import APIRouter
from typing import Dict, Any
from . import service

router = APIRouter(prefix="/core", tags=["export_snapshot"])


@router.get("/export_snapshot", response_model=Dict[str, Any])
async def export_snapshot() -> Dict[str, Any]:
    """
    Export a snapshot of all system data.
    
    Returns:
        Snapshot dict with all JSON files from backend/data
    """
    return service.snapshot()
