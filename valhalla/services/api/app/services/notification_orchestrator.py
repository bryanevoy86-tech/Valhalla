"""
PACK AG: Notification Orchestrator Service
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.notification_orchestrator import (
    NotificationChannel,
    NotificationTemplate,
    NotificationLog,
)
from app.schemas.notification_orchestrator import (
    NotificationChannelCreate,
    NotificationChannelUpdate,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationSendRequest,
)


def create_channel(db: Session, payload: NotificationChannelCreate) -> NotificationChannel:
    obj = NotificationChannel(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_channel(
    db: Session,
    channel_id: int,
    payload: NotificationChannelUpdate,
) -> Optional[NotificationChannel]:
    obj = db.query(NotificationChannel).filter(NotificationChannel.id == channel_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def list_channels(db: Session, active_only: bool = True) -> List[NotificationChannel]:
    q = db.query(NotificationChannel)
    if active_only:
        q = q.filter(NotificationChannel.is_active.is_(True))
    return q.all()


def create_template(db: Session, payload: NotificationTemplateCreate) -> NotificationTemplate:
    obj = NotificationTemplate(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_template(
    db: Session,
    template_id: int,
    payload: NotificationTemplateUpdate,
) -> Optional[NotificationTemplate]:
    obj = db.query(NotificationTemplate).filter(NotificationTemplate.id == template_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def get_template_by_key(db: Session, key: str) -> Optional[NotificationTemplate]:
    return db.query(NotificationTemplate).filter(NotificationTemplate.key == key).first()


def render_template(body: str, context: dict) -> str:
    """Simple placeholder replacement: {{key}}"""
    rendered = body
    for k, v in context.items():
        rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
    return rendered


def send_notification(
    db: Session,
    payload: NotificationSendRequest,
) -> NotificationLog:
    """Send a notification using a template"""
    tmpl = get_template_by_key(db, payload.template_key)
    if not tmpl:
        # log failure
        log = NotificationLog(
            channel_key=payload.channel_override or "unknown",
            template_key=payload.template_key,
            recipient=payload.recipient,
            subject=None,
            body="",
            status="failed",
            error_message="Template not found",
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    channel_key = payload.channel_override or tmpl.channel_key
    body = render_template(tmpl.body, payload.context)
    subject = render_template(tmpl.subject or "", payload.context) if tmpl.subject else None

    # Here you would call your real provider (email/SMS/etc.)
    # For now, treat as successfully "sent".
    status = "sent"
    error_message = None

    log = NotificationLog(
        channel_key=channel_key,
        template_key=tmpl.key,
        recipient=payload.recipient,
        subject=subject,
        body=body,
        status=status,
        error_message=error_message,
        sent_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_logs_for_recipient(db: Session, recipient: str) -> List[NotificationLog]:
    """Get all notifications sent to a recipient"""
    return (
        db.query(NotificationLog)
        .filter(NotificationLog.recipient == recipient)
        .order_by(NotificationLog.created_at.desc())
        .all()
    )
