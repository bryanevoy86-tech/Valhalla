"""
PACK AJ: Notification Bridge Service
"""

from typing import List
from sqlalchemy.orm import Session

from app.models.notification_bridge import NotificationPreference
from app.models.event_log import EventLog
from app.schemas.notification_bridge import NotificationPreferenceCreate, NotificationPreferenceUpdate, BridgeDispatchResult
from app.schemas.notification_orchestrator import NotificationSendRequest
from app.services.notification_orchestrator import send_notification


def create_preference(db: Session, payload: NotificationPreferenceCreate) -> NotificationPreference:
    obj = NotificationPreference(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_preference(db: Session, pref_id: int, payload: NotificationPreferenceUpdate) -> NotificationPreference | None:
    obj = db.query(NotificationPreference).filter(NotificationPreference.id == pref_id).first()
    if not obj:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(obj, field, value)

    db.commit()
    db.refresh(obj)
    return obj


def list_preferences_for_user(db: Session, user_id: int) -> List[NotificationPreference]:
    return (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .order_by(NotificationPreference.created_at.desc())
        .all()
    )


def get_matching_preferences(
    db: Session,
    event: EventLog,
) -> List[NotificationPreference]:
    """
    Return preferences that match this event.
    If preference.entity_type is null, it matches all entity types.
    """
    q = db.query(NotificationPreference).filter(
        NotificationPreference.event_type == event.event_type,
        NotificationPreference.is_enabled.is_(True),
    )
    # optional entity_type filter
    q = q.filter(
        (NotificationPreference.entity_type == event.entity_type)
        | (NotificationPreference.entity_type.is_(None))
    )
    return q.all()


def dispatch_notifications_for_event(
    db: Session,
    event: EventLog,
    user_ids: List[int],
) -> BridgeDispatchResult:
    """
    For a given event + list of interested user_ids, look up preferences
    and send notifications using the Notification Orchestrator.

    recipient is abstract: you might map user_id → email/phone in another layer.
    For now, we treat recipient as f"user:{user_id}" to keep it generic.
    """
    total_notifications = 0
    recipients_notified: list[int] = []

    prefs_by_user: dict[int, list[NotificationPreference]] = {uid: [] for uid in user_ids}

    # fetch all prefs for these users in one pass
    prefs = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.user_id.in_(user_ids),
            NotificationPreference.is_enabled.is_(True),
        )
        .all()
    )

    for pref in prefs:
        # event type + entity_type match check
        if pref.event_type != event.event_type:
            continue
        if pref.entity_type and pref.entity_type != event.entity_type:
            continue
        prefs_by_user[pref.user_id].append(pref)

    # send notifications
    for uid, user_prefs in prefs_by_user.items():
        if not user_prefs:
            continue

        for pref in user_prefs:
            req = NotificationSendRequest(
                template_key=pref.template_key,
                channel_override=pref.channel_key,
                recipient=f"user:{uid}",
                context={
                    "entity_type": event.entity_type,
                    "entity_id": event.entity_id,
                    "event_type": event.event_type,
                    "title": event.title or "",
                    "description": event.description or "",
                },
            )
            send_notification(db, req)
            total_notifications += 1
            if uid not in recipients_notified:
                recipients_notified.append(uid)

    return BridgeDispatchResult(
        event_id=event.id,
        notifications_created=total_notifications,
        recipients=recipients_notified,
    )
