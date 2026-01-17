"""
PACK W: System Status & Metadata Router
Endpoints for querying and updating system completion status and pack registry.
Marked as stable API (STABLE CONTRACT).
Mounted at: /system/status
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List

from app.core.db import get_db
from app.schemas.system_status import SystemStatus, SystemStatusUpdate, PackInfo
from app.services.system_status import (
    get_system_status,
    set_backend_complete,
    update_version,
    get_system_summary,
    _DEFINED_PACKS,
    count_packs_by_status,
    get_pack_by_id,
)

router = APIRouter(prefix="/system/status", tags=["System", "Metadata"])


@router.get("/", response_model=SystemStatus)
def read_system_status(db: Session = Depends(get_db)) -> SystemStatus:
    """
    Get system status including version, completion flag, and pack list.
    
    This is the primary endpoint for checking backend readiness and configuration.
    
    **STABLE CONTRACT:** Response format and keys will not change.
    
    **Response includes:**
    - version: Semantic version (major.minor.patch)
    - backend_complete: Whether backend is marked as production-ready
    - packs: List of all installed packs with status
    - summary: Human-readable description of backend functionality
    - extra: Metadata including notes and timestamps
    
    **Use cases:**
    - Heimdall can query to know which version is running
    - Frontend can check backend_complete before showing "ready" status
    - Deployment scripts can verify pack installation
    
    Args:
        db: Database session (injected)
    
    Returns:
        SystemStatus: Complete system status
    """
    status = get_system_status(db)
    return status


@router.get("/summary", response_model=Dict[str, Any])
def read_system_summary() -> Dict[str, Any]:
    """
    Get lightweight system summary (no database query required).
    
    **STABLE CONTRACT:** This endpoint will remain backwards compatible.
    
    Useful for quick status checks without full metadata queries.
    
    **Response includes:**
    - total_packs: Count of all packs
    - installed_packs: Count of installed packs
    - pending_packs: Count of pending packs
    - deprecated_packs: Count of deprecated packs
    - summary: Description of backend functionality
    
    Returns:
        Dict with pack counts and summary
    """
    summary = get_system_summary()
    return summary


@router.post("/complete", response_model=SystemStatus)
def mark_backend_complete(
    update: Optional[SystemStatusUpdate] = None,
    db: Session = Depends(get_db),
) -> SystemStatus:
    """
    Mark backend as complete/production-ready.
    
    Records timestamp and optional notes about completion.
    
    **STABLE CONTRACT:** This endpoint will not change in breaking ways.
    
    **Parameters:**
    - notes: Optional notes about the completion
    - version: Optional version update
    
    **Use cases:**
    - Deployment script marks backend as "go live"
    - Heimdall confirms backend is ready for users
    - Admin endpoint to finalize backend state
    
    **Note:** Should be protected with authentication in production.
    
    Args:
        update: SystemStatusUpdate with optional notes/version
        db: Database session (injected)
    
    Returns:
        SystemStatus: Updated system status
    """
    if update is None:
        update = SystemStatusUpdate()
    
    notes = update.notes or "Backend marked as complete"
    
    meta = set_backend_complete(db, True, notes)
    
    # Update version if provided
    if update.version:
        meta = update_version(db, update.version, notes)
    
    status = get_system_status(db)
    return status


@router.post("/incomplete", response_model=SystemStatus)
def mark_backend_incomplete(
    update: Optional[SystemStatusUpdate] = None,
    db: Session = Depends(get_db),
) -> SystemStatus:
    """
    Unmark backend as complete (revert to development status).
    
    Useful if issues are found after marking complete.
    
    **STABLE CONTRACT:** This endpoint will not change in breaking ways.
    
    **Parameters:**
    - notes: Optional notes about why completion was revoked
    
    **Use cases:**
    - Critical bug found, need to revert production status
    - Development team needs more time
    - Incident response to roll back "complete" status
    
    **Note:** Should be protected with authentication in production.
    
    Args:
        update: SystemStatusUpdate with optional notes
        db: Database session (injected)
    
    Returns:
        SystemStatus: Updated system status
    """
    if update is None:
        update = SystemStatusUpdate()
    
    notes = update.notes or "Backend marked as incomplete (development mode)"
    
    set_backend_complete(db, False, notes)
    
    status = get_system_status(db)
    return status


@router.get("/packs", response_model=Dict[str, Any])
def list_packs() -> Dict[str, Any]:
    """
    Get list of all installed packs with their status.
    
    **STABLE CONTRACT:** Response format will not change.
    
    **Response format:**
    ```json
    {
      "packs": [
        { "id": "H", "name": "...", "status": "installed" },
        ...
      ],
      "total": 16,
      "installed": 16,
      "pending": 0,
      "deprecated": 0
    }
    ```
    
    **Pack Statuses:**
    - installed: Fully implemented and active
    - pending: Planned but not yet implemented
    - deprecated: Removed or superseded
    - experimental: Test implementation
    
    Returns:
        Dict with pack list and status counts
    """
    return {
        "packs": [p.dict() for p in _DEFINED_PACKS],
        "total": len(_DEFINED_PACKS),
        "installed": count_packs_by_status("installed"),
        "pending": count_packs_by_status("pending"),
        "deprecated": count_packs_by_status("deprecated"),
    }


@router.get("/packs/{pack_id}", response_model=Dict[str, Any])
def get_pack_info(pack_id: str) -> Dict[str, Any]:
    """
    Get information about a specific pack.
    
    **STABLE CONTRACT:** Response format will not change.
    
    **Parameters:**
    - pack_id: Pack identifier (A-Z, case-insensitive)
    
    **Response includes:**
    - id: Pack identifier
    - name: Human-readable name
    - status: Current status (installed, pending, deprecated, experimental)
    
    Args:
        pack_id: Pack identifier
    
    Returns:
        Dict with pack information
    
    Raises:
        HTTPException: 404 if pack not found
    """
    pack = get_pack_by_id(pack_id.upper())
    if not pack:
        raise HTTPException(status_code=404, detail=f"Pack {pack_id} not found")
    
    return pack.dict()
