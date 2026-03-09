"""
PACK CI7: Strategic Mode Engine Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.strategic_mode import StrategicMode, ActiveMode
from app.schemas.strategic_mode import StrategicModeIn, ActiveModeSet


def upsert_mode(
    db: Session,
    payload: StrategicModeIn,
) -> StrategicMode:
    """Create or update a strategic mode by name."""
    mode = (
        db.query(StrategicMode)
        .filter(StrategicMode.name == payload.name)
        .first()
    )
    if not mode:
        mode = StrategicMode(**payload.model_dump())
        db.add(mode)
    else:
        for field, value in payload.model_dump().items():
            setattr(mode, field, value)
        mode.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(mode)
    return mode


def list_modes(db: Session) -> List[StrategicMode]:
    """List all strategic modes."""
    return (
        db.query(StrategicMode)
        .order_by(StrategicMode.created_at.asc())
        .all()
    )


def set_active_mode(
    db: Session,
    payload: ActiveModeSet,
) -> ActiveMode:
    """Set the current active mode."""
    active = db.query(ActiveMode).filter(ActiveMode.id == 1).first()
    if not active:
        active = ActiveMode(id=1, mode_name=payload.mode_name, reason=payload.reason)
        db.add(active)
    else:
        active.mode_name = payload.mode_name
        active.reason = payload.reason
        active.changed_at = datetime.utcnow()

    db.commit()
    db.refresh(active)
    return active


def get_active_mode(
    db: Session,
) -> Optional[ActiveMode]:
    """Get the current active mode."""
    return db.query(ActiveMode).filter(ActiveMode.id == 1).first()
