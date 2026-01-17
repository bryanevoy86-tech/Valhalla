"""PACK-PRELAUNCH-12: BRRRR Stability Engine Router"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from .schemas import BRRRRStabilityRead
from .service import list_stability

router = APIRouter(prefix="/brrrr", tags=["brrrr"])


@router.get("/stability", response_model=List[BRRRRStabilityRead])
def get_stability(db: Session = Depends(get_db)):
    """Get BRRRR property stability evaluations - identifies which properties are stable, need intervention, are unsafe to refi, or zones ready for expansion."""
    return list_stability(db)
