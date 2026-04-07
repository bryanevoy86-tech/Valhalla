from __future__ import annotations

from app.legal.email_config import get_legal_email_config, legal_email_config_ready
from app.legal.legal_send_service import approve_queued_send, send_queued_email


def approve_and_send_legal_document(approval_id: str) -> dict:
    ready, missing = legal_email_config_ready()
    if not ready:
        return {
            "approval_id": approval_id,
            "approved": False,
            "sent": False,
            "reason": "Missing SMTP/email configuration",
            "missing_config": missing,
        }

    approval_result = approve_queued_send(approval_id)

    cfg = get_legal_email_config()
    send_result = send_queued_email(
        approval_id=approval_id,
        smtp_host=cfg["smtp_host"],
        smtp_port=cfg["smtp_port"],
        smtp_username=cfg["smtp_username"],
        smtp_password=cfg["smtp_password"],
        sender_email=cfg["sender_email"],
        use_tls=cfg["use_tls"],
    )

    return {
        "approval_id": approval_id,
        "approved": approval_result.get("approved", False),
        "sent": send_result.get("sent", False),
        "sent_at": send_result.get("sent_at"),
    }
