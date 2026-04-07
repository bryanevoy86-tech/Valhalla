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
from app.core.engine_guard import require_engine_live
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
            
            # --- PRE-QUEUE QUALITY GATE ---
            # Extract decision metrics from webhook payload (if present)
            payload_dict = payload.payload if isinstance(payload.payload, dict) else {}
            profit = payload_dict.get("expected_profit", 0)
            roi = payload_dict.get("roi_percentage", 0)
            risk = payload_dict.get("risk_score", 100)
            
            MIN_PROFIT = 25000
            MIN_ROI = 20.0
            MAX_RISK = 15.0
            
            if profit < MIN_PROFIT or roi < MIN_ROI or risk > MAX_RISK:
                # Log but DO NOT queue
                db.add(SandboxEvent(
                    engine_name="wholesaling",
                    event_type="OUTREACH_BLOCKED_NOT_QUEUED",
                    payload_json=json.dumps({
                        "action_type": "OUTREACH_WEBHOOK",
                        "target": url,
                        "profit": profit,
                        "roi": roi,
                        "risk": risk,
                        "reason": "Failed pre-queue quality gate"
                    }),
                ))
                db.commit()
                return {
                    "ok": True,
                    "queued_for_approval": False,
                    "reason": f"Below quality threshold (profit=${profit}, roi={roi}%, risk={risk})"
                }
            
            # --- HIGH-QUALITY ONLY REACH HERE ---
            # Create a pending action (preview only, not sent yet)
            pa = PendingAction(
                engine_name="wholesaling",
                action_type="OUTREACH_WEBHOOK",
                status=PendingActionStatus.PENDING.value,
                target=url,
                preview_text=f"[SANDBOX PREVIEW] Webhook to: {url}\n\nPayload: {json.dumps(payload.payload, indent=2)}",
                payload_json=json.dumps(payload.model_dump()),
                reason="SANDBOX block → queued (passed quality gate)",
            )
            db.add(pa)

            db.add(SandboxEvent(
                engine_name="wholesaling",
                event_type="OUTREACH_BLOCKED_QUEUED",
                payload_json=json.dumps({"action_type": "OUTREACH_WEBHOOK", "target": url, "profit": profit, "roi": roi, "risk": risk}),
            ))
            db.commit()

            return {"ok": True, "queued_for_approval": True, "reason": "SANDBOX blocks real-world effects"}
        raise
    
    # --- GOVERNANCE: Check if wholesaling engine is LIVE before dispatching ---
    require_engine_live(db, "wholesaling")
    
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
            # --- PRE-QUEUE QUALITY GATE ---
            # For email, metrics would typically come from query params or headers
            # Default to conservative values if not provided
            profit = getattr(payload, 'profit', 0)
            roi = getattr(payload, 'roi', 0)
            risk = getattr(payload, 'risk', 100)
            
            MIN_PROFIT = 25000
            MIN_ROI = 20.0
            MAX_RISK = 15.0
            
            if profit < MIN_PROFIT or roi < MIN_ROI or risk > MAX_RISK:
                # Log but DO NOT queue
                db.add(SandboxEvent(
                    engine_name="wholesaling",
                    event_type="OUTREACH_BLOCKED_NOT_QUEUED",
                    payload_json=json.dumps({
                        "action_type": "OUTREACH_EMAIL",
                        "target": str(payload.to),
                        "subject": payload.subject,
                        "profit": profit,
                        "roi": roi,
                        "risk": risk,
                        "reason": "Failed pre-queue quality gate"
                    }),
                ))
                db.commit()
                return {
                    "ok": True,
                    "queued_for_approval": False,
                    "reason": f"Below quality threshold (profit=${profit}, roi={roi}%, risk={risk})"
                }
            
            # --- HIGH-QUALITY ONLY REACH HERE ---
            # Create a pending action (preview only, not sent yet)
            pa = PendingAction(
                engine_name="wholesaling",
                action_type="OUTREACH_EMAIL",
                status=PendingActionStatus.PENDING.value,
                target=str(payload.to),
                subject=payload.subject,
                preview_text=f"[SANDBOX PREVIEW] To: {payload.to}\nSubject: {payload.subject}\n\n{payload.body_text}",
                payload_json=json.dumps(payload.model_dump()),
                reason="SANDBOX block → queued (passed quality gate)",
            )
            db.add(pa)

            db.add(SandboxEvent(
                engine_name="wholesaling",
                event_type="OUTREACH_BLOCKED_QUEUED",
                payload_json=json.dumps({"action_type": "OUTREACH_EMAIL", "target": str(payload.to), "subject": payload.subject, "profit": profit, "roi": roi, "risk": risk}),
            ))
            db.commit()

            return {"ok": True, "queued_for_approval": True, "reason": "SANDBOX blocks real-world effects"}
        raise
    
    # --- GOVERNANCE: Check if wholesaling engine is LIVE before dispatching ---
    require_engine_live(db, "wholesaling")
    
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
