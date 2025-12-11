"""
PACK L0-09: Strategic Mode Service
Operational modes (aggressive, conservative, defensive, etc.).
"""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.strategic_mode import StrategicMode
from app.schemas.strategic_mode import StrategicModeCreate, StrategicModeUpdate


def create_mode(
    db: Session,
    tenant_id: str,
    payload: StrategicModeCreate,
) -> StrategicMode:
    """Create a new strategic mode."""
    mode = StrategicMode(
        tenant_id=tenant_id,
        **payload.model_dump()
    )
    db.add(mode)
    db.commit()
    db.refresh(mode)
    return mode


def list_modes(
    db: Session,
    tenant_id: str,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[StrategicMode], int]:
    """List strategic modes for a tenant."""
    query = db.query(StrategicMode).filter(StrategicMode.tenant_id == tenant_id)
    total = query.count()
    items = query.order_by(StrategicMode.created_at).offset(skip).limit(limit).all()
    return items, total


def get_mode(db: Session, mode_id: int) -> Optional[StrategicMode]:
    """Get a specific strategic mode."""
    return db.query(StrategicMode).filter(StrategicMode.id == mode_id).first()


def get_active_mode(db: Session, tenant_id: str) -> Optional[StrategicMode]:
    """Get the currently active mode for a tenant."""
    mode = (
        db.query(StrategicMode)
        .filter(
            StrategicMode.tenant_id == tenant_id,
            StrategicMode.active == True
        )
        .first()
    )
    
    # If no active mode, create a sane default
    if not mode:
        mode = create_mode(
            db,
            tenant_id,
            StrategicModeCreate(
                name="default",
                description="Default operational mode",
                parameters={
                    "risk_tolerance": 0.5,
                    "growth_weight": 0.6,
                    "speed_weight": 0.5,
                    "compliance_weight": 1.0,
                },
                active=True,
            )
        )
    
    return mode


def update_mode(
    db: Session,
    mode_id: int,
    payload: StrategicModeUpdate,
) -> Optional[StrategicMode]:
    """Update a strategic mode."""
    mode = db.query(StrategicMode).filter(StrategicMode.id == mode_id).first()
    if not mode:
        return None
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(mode, field, value)
    
    mode.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(mode)
    return mode


def set_active_mode(
    db: Session,
    tenant_id: str,
    mode_id: int,
) -> Optional[StrategicMode]:
    """
    Set a mode as active for a tenant.
    Deactivates any previously active mode.
    """
    # Deactivate all other modes
    db.query(StrategicMode).filter(
        StrategicMode.tenant_id == tenant_id,
        StrategicMode.active == True
    ).update({StrategicMode.active: False})
    
    # Activate the target mode
    mode = db.query(StrategicMode).filter(StrategicMode.id == mode_id).first()
    if not mode:
        return None
    
    mode.active = True
    mode.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(mode)
    return mode


def delete_mode(db: Session, mode_id: int) -> bool:
    """Delete a strategic mode."""
    mode = db.query(StrategicMode).filter(StrategicMode.id == mode_id).first()
    if not mode:
        return False
    
    db.delete(mode)
    db.commit()
    return True
