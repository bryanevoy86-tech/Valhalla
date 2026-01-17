from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core_gov.audit.audit_log import audit
from app.core_gov.deals.store import get_deal
from app.core_gov.deals.contact_store import add_contact, list_contacts_for_deal

router = APIRouter(prefix="/deals", tags=["Core: Deals"])

class ContactIn(BaseModel):
    channel: str  # call|text|email|dm|other
    outcome: str  # no_answer|connected|left_vm|scheduled|not_interested|bad_number|follow_up
    summary: str | None = None
    next_step: str | None = None
    meta: dict = {}

@router.post("/{deal_id}/contact")
def log_contact(deal_id: str, payload: ContactIn):
    d = get_deal(deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    c = add_contact(deal_id, payload.model_dump())
    audit("DEAL_CONTACT_LOGGED", {"deal_id": deal_id, "channel": payload.channel, "outcome": payload.outcome})
    return c

@router.get("/{deal_id}/contact")
def list_contact(deal_id: str, limit: int = 50):
    d = get_deal(deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"deal_id": deal_id, "items": list_contacts_for_deal(deal_id, limit=limit)}
