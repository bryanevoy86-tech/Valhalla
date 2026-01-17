"""
Deals router for managing deal briefs (independent of full property records).
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.match import DealBrief
from ..schemas.match import DealBriefIn, DealBriefOut

router = APIRouter(prefix="/deals", tags=["deals"])

@router.post("", response_model=DealBriefOut)
def add_deal(payload: DealBriefIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    row = DealBrief(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("", response_model=List[DealBriefOut])
def list_deals(status: str | None = None, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    q = db.query(DealBrief)
    if status:
        q = q.filter(DealBrief.status == status)
    return q.order_by(DealBrief.id.desc()).limit(500).all()
