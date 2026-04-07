"""
Buyers router for managing buyer profiles and preferences.
PERSISTENT: All buyers are stored in DB, not in-memory.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.match import Buyer, DealBrief
from ..schemas.match import BuyerIn, BuyerOut, MatchComputeOut, MatchHit
from ..core.matcher import score_buyer_vs_deal
from ..audit.service import log_event
from ..audit.schemas import AuditEventCreate

router = APIRouter(prefix="/buyers", tags=["buyers"])


@router.post("", response_model=BuyerOut)
def add_buyer(
    payload: BuyerIn, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key),
    request: Request = None
):
    """Create a new buyer and log audit event."""
    row = Buyer(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    
    # Log audit event
    try:
        log_event(db, AuditEventCreate(
            actor="system",
            action="buyer_created",
            target=f"buyer_{row.id}",
            result="success",
            meta={"buyer_id": row.id, "buyer_name": row.name}
        ))
    except Exception as e:
        print(f"Warning: Could not log audit event: {e}")
    
    return row


@router.get("", response_model=List[BuyerOut])
def list_buyers(
    active: bool | None = None, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """List all buyers, optionally filtered by active status."""
    q = db.query(Buyer)
    if active is not None:
        q = q.filter(Buyer.active.is_(active))
    return q.order_by(Buyer.id.desc()).limit(500).all()


@router.get("/{buyer_id}", response_model=BuyerOut)
def get_buyer(
    buyer_id: int, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """Get a specific buyer by ID."""
    buyer = db.get(Buyer, buyer_id)
    if not buyer:
        raise HTTPException(status_code=404, detail=f"buyer {buyer_id} not found")
    return buyer


@router.post("/{buyer_id}/toggle")
def toggle_buyer(
    buyer_id: int, 
    db: Session = Depends(get_db), 
    _: bool = Depends(require_builder_key)
):
    """Toggle buyer active status."""
    r = db.get(Buyer, buyer_id)
    if not r:
        raise HTTPException(status_code=404, detail="buyer not found")
    r.active = not r.active
    db.commit()
    db.refresh(r)
    return {"ok": True, "active": r.active}


@router.post("/match/{deal_id}", response_model=MatchComputeOut)
def match_buyer_to_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key)
):
    """
    Match a deal to all active buyers and return ranked matches.
    
    Returns:
    - mode: "deal->buyers"
    - total: number of matching buyers
    - hits: List[MatchHit] with buyer_id, buyer_name, score, reasons
    """
    # Get the deal
    deal = db.get(DealBrief, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail=f"deal {deal_id} not found")
    
    # Get all active buyers
    buyers = db.query(Buyer).filter(Buyer.active.is_(True)).all()
    
    # Score each buyer against the deal
    hits: List[MatchHit] = []
    for buyer in buyers:
        score, reasons = score_buyer_vs_deal(buyer, deal)
        if score >= 0.25:  # minimum threshold
            hits.append(MatchHit(
                buyer_id=buyer.id,
                buyer_name=buyer.name,
                score=round(score, 4),
                reasons=reasons
            ))
    
    # Sort by score descending
    hits.sort(key=lambda x: x.score, reverse=True)
    
    # Log the matching action
    try:
        log_event(db, AuditEventCreate(
            actor="system",
            action="deal_buyer_match",
            target=f"deal_{deal_id}",
            result="success",
            meta={
                "deal_id": deal_id,
                "total_matches": len(hits),
                "top_buyer_id": hits[0]["buyer_id"] if hits else None
            }
        ))
    except Exception as e:
        print(f"Warning: Could not log audit event: {e}")
    
    return MatchComputeOut(
        mode="deal->buyers",
        total=len(hits),
        hits=hits[:20]  # Return top 20
    )
