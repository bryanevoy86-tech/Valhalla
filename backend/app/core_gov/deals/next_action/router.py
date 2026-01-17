from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.core_gov.deals.store import get_deal
from app.core_gov.deals.next_action.service import next_action_for_deal

router = APIRouter(prefix="/deals", tags=["Core: Deals"])

@router.get("/{deal_id}/next_action")
def next_action(deal_id: str):
    d = get_deal(deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"deal_id": deal_id, "next": next_action_for_deal(d)}
