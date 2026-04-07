"""
PACK UG: Notification & Alert Channel Engine Router
Prefix: /system/notify
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.notification_channel import (
    NotificationChannelCreate,
    NotificationChannelOut,
    NotificationChannelList,
    NotificationCreate,
    NotificationOut,
    NotificationList,
)
from app.services.notification_channel import (
    create_channel,
    list_channels,
    enqueue_notification,
    list_notifications,
)

router = APIRouter(prefix="/system/notify", tags=["Notifications"])


@router.post("/channels", response_model=NotificationChannelOut)
def create_channel_endpoint(
    payload: NotificationChannelCreate,
    db: Session = Depends(get_db),
):
    return create_channel(db, payload)


@router.get("/channels", response_model=NotificationChannelList)
def list_channels_endpoint(
    db: Session = Depends(get_db),
):
    items = list_channels(db)
    return NotificationChannelList(total=len(items), items=items)


@router.post("/", response_model=NotificationOut)
def enqueue_notification_endpoint(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
):
    obj = enqueue_notification(db, payload)
    return obj


@router.get("/", response_model=NotificationList)
def list_notifications_endpoint(
    status: str | None = Query(None),
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    items = list_notifications(db, status=status, limit=limit)
    return NotificationList(total=len(items), items=items)
