"""
Notification queue router - queue webhooks and emails for async dispatch.
"""

import json
import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from app.core.engines.guard_runtime import enforce_engine
from app.core.engines.actions import OUTREACH
from ..core.dependencies import require_builder_key
from ..core.settings import settings
from ..models.notify import Outbox
from ..schemas.notify import WebhookQueueIn, EmailQueueIn
from app.models.pending_action import PendingAction, PendingActionStatus
from app.models.sandbox_event import SandboxEvent

router = APIRouter(prefix="/notify", tags=["notify"])


@router.post("/webhook")
def queue_webhook(
    payload: WebhookQueueIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key)
):
    """Queue a webhook notification for async dispatch."""
    try:
        enforce_engine("wholesaling", OUTREACH)
    except HTTPException as e:
        # If SANDBOX blocks real-world effects, queue an approval artifact instead
        if e.status_code == 409 and isinstance(e.detail, dict) and "EngineBlocked" in str(e.detail.get("title", "")):
            url = payload.url or settings.DEFAULT_WEBHOOK_URL
            if not url:
                raise HTTPException(status_code=400, detail="no webhook url provided or configured")
            
            # Create a pending action (preview only, not sent yet)
            pa = PendingAction(
                engine_name="wholesaling",
                action_type="OUTREACH_WEBHOOK",
                status=PendingActionStatus.PENDING.value,
                target=url,
                preview_text=f"[SANDBOX PREVIEW] Webhook to: {url}\n\nPayload: {json.dumps(payload.payload, indent=2)}",
                payload_json=json.dumps(payload.model_dump()),
                reason=str(e.detail),
            )
            db.add(pa)

            db.add(SandboxEvent(
                engine_name="wholesaling",
                event_type="OUTREACH_BLOCKED_QUEUED",
                payload_json=json.dumps({"action_type": "OUTREACH_WEBHOOK", "target": url}),
            ))
            db.commit()

            return {"ok": True, "queued_for_approval": True, "reason": "SANDBOX blocks real-world effects"}
        raise
    
    url = payload.url or settings.DEFAULT_WEBHOOK_URL
    if not url:
        raise HTTPException(
            status_code=400,
            detail="no webhook url provided or configured"
        )
    
    row = Outbox(
        kind="webhook",
        target=url,
        payload_json=json.dumps(payload.payload)
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    
    return {"ok": True, "id": row.id}


@router.post("/email")
def queue_email(
    payload: EmailQueueIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key)
):
    """Queue an email notification for async dispatch."""
    try:
        enforce_engine("wholesaling", OUTREACH)
    except HTTPException as e:
        # If SANDBOX blocks real-world effects, queue an approval artifact instead
        if e.status_code == 409 and isinstance(e.detail, dict) and "EngineBlocked" in str(e.detail.get("title", "")):
            # Create a pending action (preview only, not sent yet)
            pa = PendingAction(
                engine_name="wholesaling",
                action_type="OUTREACH_EMAIL",
                status=PendingActionStatus.PENDING.value,
                target=str(payload.to),
                subject=payload.subject,
                preview_text=f"[SANDBOX PREVIEW] To: {payload.to}\nSubject: {payload.subject}\n\n{payload.body_text}",
                payload_json=json.dumps(payload.model_dump()),
                reason=str(e.detail),
            )
            db.add(pa)

            db.add(SandboxEvent(
                engine_name="wholesaling",
                event_type="OUTREACH_BLOCKED_QUEUED",
                payload_json=json.dumps({"action_type": "OUTREACH_EMAIL", "target": str(payload.to), "subject": payload.subject}),
            ))
            db.commit()

            return {"ok": True, "queued_for_approval": True, "reason": "SANDBOX blocks real-world effects"}
        raise
    
    row = Outbox(
        kind="email",
        target=str(payload.to),
        subject=payload.subject,
        payload_json=payload.body_text
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    
    return {"ok": True, "id": row.id}
