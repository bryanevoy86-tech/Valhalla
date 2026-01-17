"""
PACK L0-09: Strategic Mode Router
Operational modes (aggressive, conservative, defensive, etc.).
Prefix: /api/v1/strategic/modes
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.strategic_mode import (
    StrategicModeCreate,
    StrategicModeUpdate,
    StrategicModeOut,
    StrategicModeList,
)
from app.services import strategic_mode as service

router = APIRouter(prefix="/api/v1/strategic/modes", tags=["Strategic Engine", "Modes"])


def get_tenant_id(request) -> str:
    """Extract tenant_id from request context."""
    # In a real app, this would come from JWT or request context
    return "default-tenant"


@router.post("", response_model=StrategicModeOut, status_code=201)
def create_mode(
    payload: StrategicModeCreate,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Create a new strategic mode."""
    return service.create_mode(db, tenant_id, payload)


@router.get("", response_model=StrategicModeList)
def list_modes_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """List strategic modes for the tenant."""
    items, total = service.list_modes(db, tenant_id, skip=skip, limit=limit)
    return StrategicModeList(total=total, items=items)


@router.get("/{mode_id}", response_model=StrategicModeOut)
def get_mode(
    mode_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific strategic mode."""
    mode = service.get_mode(db, mode_id)
    if not mode:
        raise HTTPException(status_code=404, detail="Mode not found")
    return mode


@router.patch("/{mode_id}", response_model=StrategicModeOut)
def update_mode(
    mode_id: int,
    payload: StrategicModeUpdate,
    db: Session = Depends(get_db),
):
    """Update a strategic mode."""
    mode = service.update_mode(db, mode_id, payload)
    if not mode:
        raise HTTPException(status_code=404, detail="Mode not found")
    return mode


@router.post("/{mode_id}/activate", response_model=StrategicModeOut)
def activate_mode(
    mode_id: int,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Set a mode as active for the tenant."""
    mode = service.set_active_mode(db, tenant_id, mode_id)
    if not mode:
        raise HTTPException(status_code=404, detail="Mode not found")
    return mode


@router.get("/active", response_model=StrategicModeOut)
def get_active_mode_endpoint(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id),
):
    """Get the currently active strategic mode for the tenant."""
    mode = service.get_active_mode(db, tenant_id)
    if not mode:
        raise HTTPException(status_code=404, detail="No active mode configured")
    return mode


@router.delete("/{mode_id}", status_code=204)
def delete_mode(
    mode_id: int,
    db: Session = Depends(get_db),
):
    """Delete a strategic mode."""
    success = service.delete_mode(db, mode_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mode not found")
    return None
    if not active:
        # default if never set
        active = set_active_mode(db, ActiveModeSet(mode_name="growth", reason="Default initial mode"))
    return ActiveModeOut.model_validate(active)
