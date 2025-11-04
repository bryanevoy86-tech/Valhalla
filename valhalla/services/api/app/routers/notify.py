"""
Notification queue router - queue webhooks and emails for async dispatch.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..core.dependencies import require_builder_key
from ..core.settings import settings
from ..models.notify import Outbox
from ..schemas.notify import WebhookQueueIn, EmailQueueIn

router = APIRouter(prefix="/notify", tags=["notify"])


@router.post("/webhook")
def queue_webhook(
    payload: WebhookQueueIn,
    db: Session = Depends(get_db),
    _: bool = Depends(require_builder_key)
):
    """Queue a webhook notification for async dispatch."""
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
