"""Contract provider webhook receiver (DocuSign-ready)."""
from __future__ import annotations

import uuid
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.contracts import (
    ContractEnvelope,
    Contract,
    ContractEvent,
    ContractState,
)

router = APIRouter(prefix="/api/contracts/webhooks", tags=["Contracts-Webhooks"])


def _id() -> str:
    return uuid.uuid4().hex


@router.post("/provider")
async def provider_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Provider webhook receiver.
    
    Accepts normalized payload and records status updates.
    When DocuSign adapter is installed: verify signature + parse provider payload.
    
    Expected payload:
    {
        "provider_envelope_id": "...",
        "status": "completed|declined|delivered|partially_signed",
        ...other fields
    }
    """
    payload = await request.json()

    provider_envelope_id = payload.get("provider_envelope_id")
    status = payload.get("status")
    
    if not provider_envelope_id:
        raise HTTPException(status_code=400, detail="Missing provider_envelope_id")

    env = db.query(ContractEnvelope).filter(
        ContractEnvelope.provider_envelope_id == provider_envelope_id
    ).one_or_none()
    
    if not env:
        raise HTTPException(status_code=404, detail="Unknown envelope")

    # Update envelope metadata
    env.status = status or env.status
    env.raw = payload
    env.updated_at = datetime.utcnow()

    # Update contract state based on envelope status
    c = db.query(Contract).filter(Contract.id == env.contract_id).one()
    
    if status in {"completed", "fully_executed", "signed"}:
        c.state = ContractState.FULLY_EXECUTED
    elif status in {"declined"}:
        c.state = ContractState.DECLINED
    elif status in {"delivered", "sent"}:
        c.state = ContractState.SENT_FOR_SIGNATURE
    elif status in {"partially_signed"}:
        c.state = ContractState.PARTIALLY_SIGNED
    
    c.updated_at = datetime.utcnow()

    # Record webhook event
    db.add(ContractEvent(
        id=_id(),
        contract_id=c.id,
        event_type="PROVIDER_WEBHOOK",
        actor="provider",
        meta={
            "provider_envelope_id": provider_envelope_id,
            "status": status,
            "raw": payload
        },
        created_at=datetime.utcnow(),
    ))

    db.commit()
    return {"ok": True}
