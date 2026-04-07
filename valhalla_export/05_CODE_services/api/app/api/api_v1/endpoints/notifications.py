from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.notification import Notification
from app.schemas.notifications import (
    NotificationCreate,
    NotificationUpdate,
    NotificationOut,
)

router = APIRouter()


@router.post("/", response_model=NotificationOut)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    obj = Notification(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[NotificationOut])
def list_notifications(audience: str | None = None, unread_only: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Notification)
    if audience:
        query = query.filter(Notification.audience == audience)
    if unread_only:
        query = query.filter(Notification.read.is_(False))
    return query.order_by(Notification.created_at.desc()).all()


@router.put("/{notification_id}", response_model=NotificationOut)
def update_notification(notification_id: int, payload: NotificationUpdate, db: Session = Depends(get_db)):
    obj = db.query(Notification).get(notification_id)
    if payload.read is not None:
        obj.read = payload.read
        if payload.read and not obj.read_at:
            obj.read_at = datetime.utcnow()
    if payload.read_at is not None:
        obj.read_at = payload.read_at
    db.commit()
    db.refresh(obj)
    return obj
