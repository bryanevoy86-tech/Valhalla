"""
PACK TC: Heimdall Ultra Mode Router
Exposes HTTP endpoints for configuring Heimdall Ultra Mode.
Mounted at: /heimdall/ultra
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.heimdall_ultra import UltraConfigOut, UltraConfigUpdate
from app.services.heimdall_ultra import (
    get_ultra_config,
    update_ultra_config,
    toggle_ultra_mode,
    set_initiative_level,
    set_escalation_chain,
    set_priority_matrix,
)

router = APIRouter(prefix="/heimdall/ultra", tags=["Heimdall Ultra Mode"])


@router.get("/", response_model=UltraConfigOut)
def read_ultra_config(db: Session = Depends(get_db)):
    """Retrieve current Heimdall Ultra Mode configuration."""
    return get_ultra_config(db)


@router.post("/update", response_model=UltraConfigOut)
def update_config(payload: UltraConfigUpdate, db: Session = Depends(get_db)):
    """Update Ultra Mode configuration with partial updates."""
    return update_ultra_config(db, payload)


@router.post("/enable", response_model=UltraConfigOut)
def enable_ultra(db: Session = Depends(get_db)):
    """Enable Heimdall Ultra Mode."""
    return toggle_ultra_mode(db, True)


@router.post("/disable", response_model=UltraConfigOut)
def disable_ultra(db: Session = Depends(get_db)):
    """Disable Heimdall Ultra Mode."""
    return toggle_ultra_mode(db, False)


@router.post("/initiative/{level}", response_model=UltraConfigOut)
def set_initiative(level: str, db: Session = Depends(get_db)):
    """Set initiative level: 'minimal', 'normal', or 'maximum'."""
    try:
        return set_initiative_level(db, level)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/escalation", response_model=UltraConfigOut)
def update_escalation(chain: dict, db: Session = Depends(get_db)):
    """Update escalation routing chain."""
    return set_escalation_chain(db, chain)


@router.post("/priorities", response_model=UltraConfigOut)
def update_priorities(priorities: list, db: Session = Depends(get_db)):
    """Update priority decision matrix."""
    return set_priority_matrix(db, priorities)
