from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.core_gov.deals.store import get_deal
from app.core_gov.deals.scripts_service import build_scripts

router = APIRouter(prefix="/deals", tags=["Core: Scripts"])

@router.get("/{deal_id}/scripts")
def scripts(deal_id: str, channel: str = "call"):
    d = get_deal(deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    if channel not in ("call","text","email"):
        raise HTTPException(status_code=400, detail="channel must be call|text|email")
    return build_scripts(d, channel=channel)
