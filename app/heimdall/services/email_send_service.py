from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.heimdall.models.persistence import HeimdallMessage


def send_email_message(
    db: Session,
    message_id: str,
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

    if message.status != "READY_TO_SEND":
        return {
            "status": "BLOCKED",
            "reason": "Message is not READY_TO_SEND.",
            "message_status": message.status,
        }

    payload = message.data or {}
    recipient_email = payload.get("recipient_email")

    if not recipient_email:
        return {
            "status": "BLOCKED",
            "reason": "No recipient email.",
        }

    #
    # EMAIL PROVIDER GOES HERE
    #
    # SMTP / SendGrid / Mailgun / Resend etc.
    #

    message.status = "SENT"
    message.data = {
        **payload,
        "sent_at": datetime.utcnow().isoformat(),
        "delivery_method": "email",
    }
    db.commit()
    db.refresh(message)

    return {
        "status": "EMAIL_SENT",
        "message_id": message.id,
        "recipient_email": recipient_email,
    }
