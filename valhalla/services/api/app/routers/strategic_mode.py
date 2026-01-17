"""
PACK CI7: Strategic Mode Engine Router
Prefix: /intelligence/modes
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.strategic_mode import (
    StrategicModeIn,
    StrategicModeOut,
    StrategicModeList,
    ActiveModeSet,
    ActiveModeOut,
)
from app.services.strategic_mode import (
    upsert_mode,
    list_modes,
    set_active_mode,
    get_active_mode,
)

router = APIRouter(prefix="/intelligence/modes", tags=["Intelligence", "Modes"])


@router.post("/", response_model=StrategicModeOut)
def upsert_mode_endpoint(
    payload: StrategicModeIn,
    db: Session = Depends(get_db),
):
    """Create or update a strategic mode."""
    return upsert_mode(db, payload)


@router.get("/", response_model=StrategicModeList)
def list_modes_endpoint(
    db: Session = Depends(get_db),
):
    """List all strategic modes."""
    items = list_modes(db)
    return StrategicModeList(total=len(items), items=items)


@router.post("/active", response_model=ActiveModeOut)
def set_active_mode_endpoint(
    payload: ActiveModeSet,
    db: Session = Depends(get_db),
):
    """Set the active strategic mode."""
    active = set_active_mode(db, payload)
    return ActiveModeOut.model_validate(active)


@router.get("/active", response_model=ActiveModeOut)
def get_active_mode_endpoint(
    db: Session = Depends(get_db),
):
    """Get the currently active strategic mode."""
    active = get_active_mode(db)
    if not active:
        # default if never set
        active = set_active_mode(db, ActiveModeSet(mode_name="growth", reason="Default initial mode"))
    return ActiveModeOut.model_validate(active)
