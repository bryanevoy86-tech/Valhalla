from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core_gov.audit.audit_log import audit
from app.core_gov.deals.store import get_deal
from app.core_gov.followups.store import create_followup, update_followup, queue

router = APIRouter(prefix="/followups", tags=["Core: Followups"])

class FollowupIn(BaseModel):
    deal_id: str
    due_at_utc: str  # ISO string
    action: str      # call|text|email|visit|review
    note: str | None = None
    priority: str = "medium"  # low|medium|high
    meta: dict = {}

class FollowupPatch(BaseModel):
    status: str | None = None  # done|canceled|open
    note: str | None = None

@router.post("/create")
def create(payload: FollowupIn):
    d = get_deal(payload.deal_id)
    if not d:
        raise HTTPException(status_code=404, detail="Deal not found")
    fu = create_followup(payload.model_dump())
    audit("FOLLOWUP_CREATED", {"deal_id": payload.deal_id, "due_at_utc": payload.due_at_utc, "action": payload.action})
    return fu

@router.patch("/{fu_id}")
def patch(fu_id: str, payload: FollowupPatch):
    fu = update_followup(fu_id, {k: v for k, v in payload.model_dump().items() if v is not None})
    if not fu:
        raise HTTPException(status_code=404, detail="Followup not found")
    audit("FOLLOWUP_UPDATED", {"fu_id": fu_id, "status": fu.get("status")})
    return fu

@router.get("/queue")
def get_queue(limit: int = 50, due_before_utc: str | None = None, status: str = "open"):
    return {"items": queue(limit=limit, due_before_utc=due_before_utc, status=status)}
