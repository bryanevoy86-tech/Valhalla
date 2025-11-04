"""
Match router for computing buyer-deal matches with intelligent scoring.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..models.match import Buyer, DealBrief
from ..schemas.match import MatchComputeIn, MatchComputeOut, MatchHit, DealHit
from ..core.matcher import score_buyer_vs_deal

router = APIRouter(prefix="/match", tags=["match"])

@router.post("/compute", response_model=MatchComputeOut)
def compute(payload: MatchComputeIn, db: Session = Depends(get_db), _: bool = Depends(require_builder_key)):
    # Mode A: deal -> buyers
    if payload.deal_id or payload.deal:
        if payload.deal_id:
            deal = db.get(DealBrief, payload.deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="deal not found")
        else:
            deal = DealBrief(**payload.deal.model_dump())  # transient
        rows = db.query(Buyer).filter(Buyer.active.is_(True)).all()
        hits: List[MatchHit] = []
        for b in rows:
            s, why = score_buyer_vs_deal(b, deal)
            if s >= payload.min_score:
                hits.append(MatchHit(buyer_id=b.id, buyer_name=b.name, score=round(s,4), reasons=why))
        hits.sort(key=lambda x: x.score, reverse=True)
        return MatchComputeOut(mode="deal->buyers", total=len(hits), hits=hits[:payload.limit])

    # Mode B: buyer -> deals
    if payload.buyer_id:
        b = db.get(Buyer, payload.buyer_id)
        if not b:
            raise HTTPException(status_code=404, detail="buyer not found")
        deals = db.query(DealBrief).filter(DealBrief.status == "active").all()
        hits: List[DealHit] = []
        for d in deals:
            s, why = score_buyer_vs_deal(b, d)
            if s >= payload.min_score:
                hits.append(DealHit(deal_id=d.id, headline=d.headline, score=round(s,4), reasons=why))
        hits.sort(key=lambda x: x.score, reverse=True)
        return MatchComputeOut(mode="buyer->deals", total=len(hits), hits=hits[:payload.limit])

    raise HTTPException(status_code=400, detail="provide deal_id or deal payload, or buyer_id")
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return {"lead_id": lead_id, "results": ranked[:10]}
