from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.models.persistence import HeimdallMessage


def log_message_delivery(
    db: Session,
    message_id: str,
    delivery_payload: Dict[str, Any],
) -> Dict[str, Any]:

    message = (
        db.query(HeimdallMessage)
        .filter(HeimdallMessage.id == message_id)
        .first()
    )

    if not message:
        return {
            "status": "ERROR",
            "reason": "Message not found.",
        }

    existing = message.data or {}

    existing["delivery_tracking"] = {
        "delivered": delivery_payload.get("delivered"),
        "delivery_time": datetime.utcnow().isoformat(),
        "provider_status": delivery_payload.get("provider_status"),
        "provider_message_id": delivery_payload.get(
            "provider_message_id"
        ),
    }

    message.data = existing

    if delivery_payload.get("delivered"):
        message.status = "DELIVERED"

    db.commit()
    db.refresh(message)

    return {
        "status": "DELIVERY_LOGGED",
        "message_id": message.id,
    }


def log_message_reply(
    db: Session,
    message_id: str,
    reply_payload: Dict[str, Any],
) -> Dict[str, Any]:

    message = (
        db.query(HeimdallMessage)
        .filter(HeimdallMessage.id == message_id)
        .first()
    )

    if not message:
        return {
            "status": "ERROR",
            "reason": "Message not found.",
        }

    existing = message.data or {}

    existing["reply_tracking"] = {
        "reply_received": True,
        "reply_text": reply_payload.get("reply_text"),
        "reply_channel": reply_payload.get("reply_channel"),
        "reply_time": datetime.utcnow().isoformat(),
    }

    message.data = existing
    message.status = "REPLIED"

    db.commit()
    db.refresh(message)

    return {
        "status": "REPLY_LOGGED",
        "message_id": message.id,
    }
