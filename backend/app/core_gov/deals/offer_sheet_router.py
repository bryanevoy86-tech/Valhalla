from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.core_gov.deals.store import get_deal
from app.core_gov.deals.offer_sheet_service import build_offer_sheet

router = APIRouter(prefix="/deals", tags=["Core: Deals"])

@router.get("/{deal_id}/offer_sheet")
def offer_sheet(deal_id: str):
    d = get_deal(deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    return build_offer_sheet(d)
