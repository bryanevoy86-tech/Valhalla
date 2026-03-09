"""PACK-PRELAUNCH-10: EIA Guardian Engine Router"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from .schemas import EIAStatusRead
from .service import get_status

router = APIRouter(prefix="/eia", tags=["eia"])


@router.get("/status", response_model=EIAStatusRead)
def read_status(db: Session = Depends(get_db)):
    """Get current EIA status - monitors compliance and risk before system profitability."""
    return get_status(db)
