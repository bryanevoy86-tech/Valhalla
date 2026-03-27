"""
EIA Month Lifecycle Router - Mounted at /exports
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.eia_export import (
    open_eia_month,
    EIAMonthManager,
)
from app.schemas.eia_export import MonthStatusResponse, MonthOpenResponse


router = APIRouter(
    prefix="/exports",
    tags=["Exports & Month"]
)


@router.get("/month/status", response_model=dict)
async def get_month_status(
    year: int,
    month: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get the status of an EIA month.
    
    Returns whether month is open or closed/locked.
    
    Args:
        year: Fiscal year
        month: Month number (1-12)
        db: Database session
    
    Returns:
        Dict with month status including locked state
    """
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    try:
        manager = EIAMonthManager(db)
        status = manager.get_month_status(year, month)
        return status
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get month status: {str(e)}")


@router.post("/month/open", response_model=dict)
async def open_month(
    year: int,
    month: int,
    opened_by: str = "system",
    db: Session = Depends(get_db),
) -> dict:
    """
    Open an EIA month for new entries.
    
    Unlocks a previously closed/locked month, allowing new entries to be added.
    
    Args:
        year: Fiscal year
        month: Month number (1-12)
        opened_by: User/system identifier
        db: Database session
    
    Returns:
        Dict with open confirmation
    """
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    
    try:
        result = open_eia_month(db, year, month, opened_by)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to open month: {str(e)}")
