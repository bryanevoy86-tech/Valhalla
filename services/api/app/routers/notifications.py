from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.notifications.service import NotificationService
from app.notifications.schemas import Notification, NotificationOut, NotificationCreate
from app.core.db import get_db


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/create", response_model=NotificationOut)
async def create_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """Create a new notification for a user."""
    result = NotificationService.create_notification(
        user_id=notification.user_id,
        content=notification.content
    )
    return result


@router.get("/list", response_model=List[NotificationOut])
async def list_notifications(
    user_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get notifications, optionally filtered by user_id.
    Returns most recent notifications first.
    """
    return NotificationService.get_notifications(user_id=user_id or None, limit=limit)


@router.post("/mark-read/{user_id}/{index}")
async def mark_notification_read(
    user_id: str,
    index: int,
    db: Session = Depends(get_db)
):
    """Mark a specific notification as read for a user."""
    success = NotificationService.mark_as_read(user_id=user_id, index=index)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True, "message": "Notification marked as read"}


@router.get("/unread-count/{user_id}")
async def get_unread_count(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get count of unread notifications for a user."""
    count = NotificationService.get_unread_count(user_id=user_id)
    return {"user_id": user_id, "unread_count": count}
