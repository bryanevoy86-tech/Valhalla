from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.core_gov.deals.store import get_deal
from app.core_gov.deals.scoring.service import score_deal

router = APIRouter(prefix="/deals", tags=["Core: Deals"])

@router.get("/{deal_id}/score")
def score(deal_id: str):
    d = get_deal(deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"deal_id": deal_id, "score": score_deal(d)}
