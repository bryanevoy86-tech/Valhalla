"""
PACK AJ: Notification Bridge Router
Prefix: /notification-bridge
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.notification_bridge import (
    NotificationPreferenceCreate,
    NotificationPreferenceUpdate,
    NotificationPreferenceOut,
    BridgeDispatchResult,
)
from app.services.notification_bridge import (
    create_preference,
    update_preference,
    list_preferences_for_user,
    dispatch_notifications_for_event,
)
from app.models.event_log import EventLog

router = APIRouter(prefix="/notification-bridge", tags=["NotificationBridge"])


@router.post("/preferences", response_model=NotificationPreferenceOut)
def create_preference_endpoint(
    payload: NotificationPreferenceCreate,
    db: Session = Depends(get_db),
):
    """Create a notification preference for a user."""
    return create_preference(db, payload)


@router.get("/preferences/by-user/{user_id}", response_model=List[NotificationPreferenceOut])
def list_preferences_for_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
):
    """List all notification preferences for a user."""
    return list_preferences_for_user(db, user_id)


@router.patch("/preferences/{pref_id}", response_model=NotificationPreferenceOut)
def update_preference_endpoint(
    pref_id: int,
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
):
    """Update a notification preference."""
    obj = update_preference(db, pref_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Preference not found")
    return obj


@router.post("/dispatch/{event_id}", response_model=BridgeDispatchResult)
def dispatch_for_event_endpoint(
    event_id: int,
    user_ids: list[int] = Query(..., description="Users to evaluate for this event"),
    db: Session = Depends(get_db),
):
    """Dispatch notifications for an event to specified users."""
    event = db.query(EventLog).filter(EventLog.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return dispatch_notifications_for_event(db, event, user_ids)
