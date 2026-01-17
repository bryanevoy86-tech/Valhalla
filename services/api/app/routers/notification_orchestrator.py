"""
PACK AG: Notification Orchestrator Router
Prefix: /notifications
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.notification_orchestrator import (
    NotificationChannelCreate,
    NotificationChannelUpdate,
    NotificationChannelOut,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateOut,
    NotificationSendRequest,
    NotificationLogOut,
)
from app.services.notification_orchestrator import (
    create_channel,
    update_channel,
    list_channels,
    create_template,
    update_template,
    get_template_by_key,
    send_notification,
    list_logs_for_recipient,
)

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/channels", response_model=NotificationChannelOut)
def create_channel_endpoint(
    payload: NotificationChannelCreate,
    db: Session = Depends(get_db),
):
    """Create a new notification channel"""
    return create_channel(db, payload)


@router.get("/channels", response_model=List[NotificationChannelOut])
def list_channels_endpoint(
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
):
    """List all notification channels"""
    return list_channels(db, active_only=active_only)


@router.patch("/channels/{channel_id}", response_model=NotificationChannelOut)
def update_channel_endpoint(
    channel_id: int,
    payload: NotificationChannelUpdate,
    db: Session = Depends(get_db),
):
    """Update a notification channel"""
    obj = update_channel(db, channel_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Channel not found")
    return obj


@router.post("/templates", response_model=NotificationTemplateOut)
def create_template_endpoint(
    payload: NotificationTemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a new notification template"""
    return create_template(db, payload)


@router.patch("/templates/{template_id}", response_model=NotificationTemplateOut)
def update_template_endpoint(
    template_id: int,
    payload: NotificationTemplateUpdate,
    db: Session = Depends(get_db),
):
    """Update a notification template"""
    obj = update_template(db, template_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Template not found")
    return obj


@router.get("/templates/{key}", response_model=NotificationTemplateOut)
def get_template_endpoint(
    key: str,
    db: Session = Depends(get_db),
):
    """Get a template by key"""
    tmpl = get_template_by_key(db, key)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tmpl


@router.post("/send", response_model=NotificationLogOut)
def send_notification_endpoint(
    payload: NotificationSendRequest,
    db: Session = Depends(get_db),
):
    """Send a notification using a template"""
    return send_notification(db, payload)


@router.get("/logs/by-recipient", response_model=List[NotificationLogOut])
def list_logs_recipient_endpoint(
    recipient: str = Query(...),
    db: Session = Depends(get_db),
):
    """Get all notifications sent to a recipient"""
    return list_logs_for_recipient(db, recipient)
