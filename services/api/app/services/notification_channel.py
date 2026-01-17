"""
PACK UG: Notification & Alert Channel Engine Service
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.notification_channel import NotificationChannel, NotificationOutbox
from app.schemas.notification_channel import (
    NotificationChannelCreate,
    NotificationCreate,
)


def create_channel(db: Session, payload: NotificationChannelCreate) -> NotificationChannel:
    obj = NotificationChannel(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_channels(db: Session) -> List[NotificationChannel]:
    return db.query(NotificationChannel).order_by(NotificationChannel.created_at.desc()).all()


def enqueue_notification(
    db: Session,
    payload: NotificationCreate,
) -> NotificationOutbox:
    obj = NotificationOutbox(
        channel_id=payload.channel_id,
        subject=payload.subject,
        body=payload.body,
        payload=payload.payload,
        status="pending",
        attempts=0,
        created_at=datetime.utcnow(),
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_notifications(
    db: Session,
    status: Optional[str] = None,
    limit: int = 200,
) -> List[NotificationOutbox]:
    q = db.query(NotificationOutbox)
    if status:
        q = q.filter(NotificationOutbox.status == status)
    return (
        q.order_by(NotificationOutbox.created_at.desc())
        .limit(limit)
        .all()
    )
