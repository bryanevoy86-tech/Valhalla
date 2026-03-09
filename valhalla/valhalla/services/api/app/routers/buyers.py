"""
Buyers router for managing buyer profiles and preferences.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.match import Buyer
from ..schemas.match import BuyerIn, BuyerOut

router = APIRouter(prefix="/buyers", tags=["buyers"])

@router.post("", response_model=BuyerOut)
def add_buyer(payload: BuyerIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    row = Buyer(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("", response_model=List[BuyerOut])
def list_buyers(active: bool | None = None, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    q = db.query(Buyer)
    if active is not None:
        q = q.filter(Buyer.active.is_(active))
    return q.order_by(Buyer.id.desc()).limit(500).all()

@router.post("/{buyer_id}/toggle")
def toggle_buyer(buyer_id: int, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    r = db.get(Buyer, buyer_id)
    if not r:
        raise HTTPException(status_code=404, detail="buyer not found")
    r.active = not r.active
    db.commit()
    db.refresh(r)
    return {"ok": True, "active": r.active}
