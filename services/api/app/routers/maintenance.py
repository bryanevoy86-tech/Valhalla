"""
PACK UE: Maintenance Window & Freeze Switch Router
Prefix: /system/maintenance
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.maintenance import (
    MaintenanceWindowCreate,
    MaintenanceWindowOut,
    MaintenanceWindowList,
    MaintenanceStateOut,
)
from app.services.maintenance import (
    create_maintenance_window,
    list_maintenance_windows,
    get_maintenance_state,
    set_maintenance_mode,
)

router = APIRouter(prefix="/system/maintenance", tags=["Maintenance"])


@router.post("/windows", response_model=MaintenanceWindowOut)
def create_window_endpoint(
    payload: MaintenanceWindowCreate,
    db: Session = Depends(get_db),
):
    if payload.ends_at <= payload.starts_at:
        raise HTTPException(status_code=400, detail="ends_at must be after starts_at")
    return create_maintenance_window(db, payload)


@router.get("/windows", response_model=MaintenanceWindowList)
def list_windows_endpoint(
    db: Session = Depends(get_db),
):
    items = list_maintenance_windows(db)
    return MaintenanceWindowList(total=len(items), items=items)


@router.get("/state", response_model=MaintenanceStateOut)
def get_state_endpoint(
    db: Session = Depends(get_db),
):
    state = get_maintenance_state(db)
    return MaintenanceStateOut(
        mode=state.mode,
        reason=state.reason,
        updated_at=state.updated_at,
    )


@router.post("/state/{mode}", response_model=MaintenanceStateOut)
def set_state_endpoint(
    mode: str,
    reason: str | None = None,
    db: Session = Depends(get_db),
):
    if mode not in {"normal", "maintenance", "read_only"}:
        raise HTTPException(status_code=400, detail="Invalid maintenance mode")
    state = set_maintenance_mode(db, mode, reason)
    return MaintenanceStateOut(
        mode=state.mode,
        reason=state.reason,
        updated_at=state.updated_at,
    )
