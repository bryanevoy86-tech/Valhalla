"""
PACK UE: Maintenance Window & Freeze Switch Service
"""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session

from app.models.maintenance import MaintenanceWindow, MaintenanceState
from app.schemas.maintenance import MaintenanceWindowCreate


def create_maintenance_window(
    db: Session,
    payload: MaintenanceWindowCreate,
) -> MaintenanceWindow:
    obj = MaintenanceWindow(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_maintenance_windows(db: Session) -> List[MaintenanceWindow]:
    return (
        db.query(MaintenanceWindow)
        .order_by(MaintenanceWindow.starts_at.desc())
        .all()
    )


def _ensure_state_row(db: Session) -> MaintenanceState:
    state = db.query(MaintenanceState).filter(MaintenanceState.id == 1).first()
    if not state:
        state = MaintenanceState(id=1, mode="normal", reason="Initialized")
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def get_maintenance_state(db: Session) -> MaintenanceState:
    return _ensure_state_row(db)


def set_maintenance_mode(
    db: Session,
    mode: str,
    reason: str | None = None,
) -> MaintenanceState:
    state = _ensure_state_row(db)
    state.mode = mode
    if reason is not None:
        state.reason = reason
    state.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(state)
    return state
