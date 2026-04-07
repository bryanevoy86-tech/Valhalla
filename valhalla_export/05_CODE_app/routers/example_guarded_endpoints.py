"""
Example: Properly guarded side-effect endpoint pattern.

Copy this template for every endpoint that touches the real world.
DO NOT modify the guard logic—only the business logic.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.engines.require import require
from app.core.engines.actions import OUTREACH, DISPOSITION_SEND, CONTRACT_SEND

router = APIRouter(prefix="/api/example", tags=["example"])


class SendOutreachBody(BaseModel):
    contact_id: str
    message: str
    channel: str  # "sms" | "email" | "call"


@router.post("/send-outreach")
def send_outreach(body: SendOutreachBody):
    """
    Send outreach to contact.
    
    ⚠️ THIS IS A REAL-WORLD EFFECT
    Must be guarded by require() with OUTREACH action.
    
    If engine state is SANDBOX → 409 EngineBlocked
    If engine state is ACTIVE → proceeds (if runbook clear)
    """
    # FIRST LINE: Guard the endpoint
    require("wholesaling", OUTREACH)
    
    # Now safe to proceed with the send logic
    try:
        # ... send logic here (SMS/email/call provider call, etc.)
        return {
            "ok": True,
            "contact_id": body.contact_id,
            "channel": body.channel,
            "message": body.message,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-disposition")
def send_disposition(body: BaseModel):
    """Send disposition to buyer/listing platform."""
    require("wholesaling", DISPOSITION_SEND)
    # ... proceed
    pass


@router.post("/send-contract")
def send_contract(body: BaseModel):
    """Send contract for signature."""
    require("wholesaling", CONTRACT_SEND)
    # ... proceed
    pass


@router.get("/scoring")
def compute_score(entity_id: str):
    """
    Compute score (read-only, no guard needed).
    Safe in SANDBOX.
    """
    # No require() call needed—this is safe computation
    return {"entity_id": entity_id, "score": 95.0}
