from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.core_gov.deals.store import get_deal
from app.core_gov.buyers.match import match_buyers_to_deal

router = APIRouter(prefix="/deals", tags=["Core: Buyers"])

@router.get("/{deal_id}/match_buyers")
def match(deal_id: str, limit: int = 10):
    d = get_deal(deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"deal_id": deal_id, "items": match_buyers_to_deal(d, limit=limit)}
