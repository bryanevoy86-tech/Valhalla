"""PACK-PRELAUNCH-11: Arbitrage Guard Engine Router"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from .schemas import ArbitrageSettingsRead, ArbitrageSettingsUpdate
from .service import get_settings, update_settings

router = APIRouter(prefix="/arbitrage", tags=["arbitrage"])


@router.get("/status", response_model=ArbitrageSettingsRead)
def status(db: Session = Depends(get_db)):
    """Get current arbitrage settings and mode (SAFE/NORMAL/AGGRESSIVE)."""
    return get_settings(db)


@router.patch("/status", response_model=ArbitrageSettingsRead)
def update_status(payload: ArbitrageSettingsUpdate, db: Session = Depends(get_db)):
    """Update arbitrage settings and risk parameters."""
    return update_settings(db, payload)
