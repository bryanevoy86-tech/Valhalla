"""PACK 62: Capital Allocation Router
API endpoints for capital allocation operations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.capital_allocation_service import save_allocation, latest_allocation
from app.schemas.capital_allocation import CapitalAllocationOut

router = APIRouter(prefix="/capital-allocation", tags=["Capital Allocation"])


@router.post("/", response_model=CapitalAllocationOut)
def set_allocation(
    arbitrage_pct: float,
    vault_pct: float,
    shield_pct: float,
    db: Session = Depends(get_db)
):
    """Set new capital allocation percentages."""
    return save_allocation(db, arbitrage_pct, vault_pct, shield_pct)


@router.get("/", response_model=CapitalAllocationOut)
def get_allocation(db: Session = Depends(get_db)):
    """Get the latest capital allocation."""
    return latest_allocation(db)
