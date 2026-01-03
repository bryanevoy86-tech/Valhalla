from __future__ import annotations

from fastapi import APIRouter
from app.core_gov.audit.audit_log import audit
from app.core_gov.buyers.models import BuyerIn, Buyer
from app.core_gov.buyers.store import add_buyer, list_buyers

router = APIRouter(prefix="/buyers", tags=["Core: Buyers"])

@router.post("", response_model=Buyer)
def create(payload: BuyerIn):
    b = add_buyer(payload.model_dump())
    audit("BUYER_CREATED", {"id": b["id"], "name": b["name"], "country": b.get("country")})
    return b

@router.get("")
def list_(limit: int = 50, country: str | None = None):
    return {"items": list_buyers(limit=limit, country=country)}
