"""
Capital router - tracks incoming funds from various sources.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..core.db import get_db
from ..schemas.capital import CapitalIn, CapitalOut
from ..models.capital import CapitalIntake
from ..core.dependencies import require_builder_key

router = APIRouter(prefix="/capital", tags=["capital"])


@router.post("/intake", status_code=status.HTTP_201_CREATED, response_model=CapitalOut)
async def create_capital_intake(
    data: CapitalIn,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_builder_key)
):
    """
    Record a new capital intake event. Requires builder API key authentication.
    
    Use this to track incoming funds from wholesaling, flips, FX trading, etc.
    """
    intake = CapitalIntake(
        source=data.source,
        currency=data.currency,
        amount=data.amount,
        note=data.note
    )
    db.add(intake)
    db.commit()
    db.refresh(intake)
    
    return intake


@router.get("/intake", response_model=List[CapitalOut])
async def list_capital_intake(
    limit: int = 200,
    db: Session = Depends(get_db),
    _auth: None = Depends(require_builder_key)
):
    """
    List recent capital intake records. Requires builder API key authentication.
    
    Returns up to 200 most recent records, ordered by created_at descending.
    """
    records = (
        db.query(CapitalIntake)
        .order_by(CapitalIntake.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )
    
    return records
