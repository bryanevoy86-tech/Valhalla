from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core_gov.deals.store import get_deal
from app.core_gov.deals.disposition_service import build_disposition_package

router = APIRouter(prefix="/deals", tags=["Core: Disposition"])

@router.get("/{deal_id}/disposition_package")
def disposition_package(deal_id: str, buyer_limit: int = 10):
    d = get_deal(deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    return build_disposition_package(d, buyer_limit=buyer_limit)
