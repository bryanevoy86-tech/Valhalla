"""Receive signed normalized events from the configured signature gateway."""

import hashlib
import hmac
import json
import os
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.contracts import Contract, ContractEnvelope, ContractEvent, ContractState, SignProvider

router = APIRouter(prefix="/api/contracts/webhooks", tags=["Contracts-Webhooks"])

STATE_BY_STATUS = {
    "sent": ContractState.SENT_FOR_SIGNATURE,
    "delivered": ContractState.SENT_FOR_SIGNATURE,
    "partially_signed": ContractState.PARTIALLY_SIGNED,
    "declined": ContractState.DECLINED,
    "signed": ContractState.FULLY_EXECUTED,
    "completed": ContractState.FULLY_EXECUTED,
    "fully_executed": ContractState.FULLY_EXECUTED,
}
STATE_ORDER = {
    ContractState.SENT_FOR_SIGNATURE: 0,
    ContractState.PARTIALLY_SIGNED: 1,
    ContractState.DECLINED: 2,
    ContractState.FULLY_EXECUTED: 2,
}


@router.post("/provider")
async def provider_webhook(request: Request, db: Session = Depends(get_db)):
    secret = os.getenv("VALHALLA_CONTRACT_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=503, detail="Verified signature gateway is unavailable")
    body = await request.body()
    provided = request.headers.get("X-Contract-Signature", "")
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid signature gateway authentication")
    try:
        event = json.loads(body)
    except (ValueError, UnicodeError):
        raise HTTPException(status_code=422, detail="Invalid signature event") from None
    if not isinstance(event, dict):
        raise HTTPException(status_code=422, detail="Invalid signature event")
    envelope_id, status = event.get("provider_envelope_id"), event.get("status")
    if not isinstance(envelope_id, str) or not envelope_id or not isinstance(status, str) or status not in STATE_BY_STATUS:
        raise HTTPException(status_code=422, detail="Known envelope ID and status are required")

    envelope = db.query(ContractEnvelope).filter_by(
        provider=SignProvider.DOCUSIGN, provider_envelope_id=envelope_id,
    ).with_for_update().one_or_none()
    if not envelope:
        raise HTTPException(status_code=404, detail="Unknown provider envelope")
    contract = db.get(Contract, envelope.contract_id, with_for_update=True)
    if contract is None or contract.active_envelope_id != envelope.id or contract.sign_provider != envelope.provider:
        raise HTTPException(status_code=409, detail="Envelope does not match the active contract")
    state = STATE_BY_STATUS[status]
    previous = STATE_ORDER.get(contract.state)
    if previous is None:
        raise HTTPException(status_code=409, detail="Contract is not awaiting a signature event")
    if STATE_ORDER[state] <= previous:
        return {"ok": True, "applied": False, "state": contract.state.value}

    now = datetime.utcnow()
    envelope.status, envelope.raw, envelope.updated_at = status, event, now
    contract.state, contract.updated_at = state, now
    db.add(ContractEvent(
        id=uuid4().hex, contract_id=contract.id, event_type="PROVIDER_WEBHOOK", actor="verified_gateway",
        meta={"provider_envelope_id": envelope_id, "status": status, "body_sha256": hashlib.sha256(body).hexdigest()},
    ))
    db.commit()
    return {"ok": True, "applied": True, "state": contract.state.value}
