from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core_gov.audit.audit_log import audit
from app.core_gov.deals.models import DealIn, Deal
from app.core_gov.deals.store import add_deal, list_deals, get_deal, update_deal

router = APIRouter(prefix="/deals", tags=["Core: Deals"])

class DealPatch(BaseModel):
    stage: str | None = None
    notes: str | None = None
    tags: list[str] | None = None
    mao: float | None = None
    arv: float | None = None
    asking_price: float | None = None
    est_repairs: float | None = None
    meta: dict | None = None

@router.post("", response_model=Deal)
def create(payload: DealIn):
    deal = add_deal(payload.model_dump())
    audit("DEAL_CREATED", {"id": deal["id"], "strategy": deal.get("strategy"), "source": deal.get("lead_source")})
    return deal

@router.get("")
def list_(limit: int = 50, stage: str | None = None, source: str | None = None):
    return {"items": list_deals(limit=limit, stage=stage, source=source)}

@router.get("/{deal_id}")
def get_(deal_id: str):
    d = get_deal(deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    return d

@router.patch("/{deal_id}")
def patch(deal_id: str, payload: DealPatch):
    d = update_deal(deal_id, {k: v for k, v in payload.model_dump().items() if v is not None})
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    audit("DEAL_UPDATED", {"id": deal_id})
    return d
