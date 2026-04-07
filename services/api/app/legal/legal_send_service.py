from __future__ import annotations

import json
import smtplib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from app.legal.document_engine import generate_document
from app.legal.legal_audit_log import write_legal_audit

BASE_DIR = Path(__file__).resolve().parent
QUEUE_DIR = BASE_DIR / "send_queue"
QUEUE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class QueuedLegalSend:
    approval_id: str
    template_key: str
    recipients: list[str]
    cc: list[str]
    subject: str
    body_intro: str
    document_path: str
    payload: dict[str, Any]
    approved: bool
    sent: bool
    created_at: str
    sent_at: str | None = None


def _queue_path(approval_id: str) -> Path:
    return QUEUE_DIR / f"{approval_id}.json"


def queue_legal_document(
    approval_id: str,
    template_key: str,
    payload: dict[str, Any],
    recipients: list[str],
    cc: list[str] | None = None,
    body_intro: str | None = None,
) -> dict[str, Any]:
    cc = cc or []
    body_intro = body_intro or "Attached is the draft document for review and finalization."

    generated = generate_document(template_key, payload)

    item = QueuedLegalSend(
        approval_id=approval_id,
        template_key=template_key,
        recipients=recipients,
        cc=cc,
        subject=generated.subject,
        body_intro=body_intro,
        document_path=generated.output_path,
        payload=payload,
        approved=False,
        sent=False,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _queue_path(approval_id).write_text(json.dumps(asdict(item), indent=2), encoding="utf-8")

    result = {
        "approval_id": approval_id,
        "queued": True,
        "missing_fields": generated.missing_fields,
        "document_path": generated.output_path,
        "subject": generated.subject,
    }
    write_legal_audit("queued", approval_id, result)
    return result


def approve_queued_send(approval_id: str) -> dict[str, Any]:
    path = _queue_path(approval_id)
    if not path.exists():
        raise FileNotFoundError(f"Approval item not found: {approval_id}")

    data = json.loads(path.read_text(encoding="utf-8"))
    data["approved"] = True
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = {"approval_id": approval_id, "approved": True}
    write_legal_audit("approved", approval_id, result)
    return result


def send_queued_email(
    approval_id: str,
    smtp_host: str,
    smtp_port: int,
    smtp_username: str,
    smtp_password: str,
    sender_email: str,
    use_tls: bool = True,
) -> dict[str, Any]:
    path = _queue_path(approval_id)
    if not path.exists():
        raise FileNotFoundError(f"Approval item not found: {approval_id}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not data.get("approved", False):
        result = {"approval_id": approval_id, "sent": False, "reason": "Not approved"}
        write_legal_audit("send_blocked", approval_id, result)
        return result

    msg = EmailMessage()
    msg["From"] = sender_email
    msg["To"] = ", ".join(data["recipients"])
    if data["cc"]:
        msg["Cc"] = ", ".join(data["cc"])
    msg["Subject"] = data["subject"]

    msg.set_content(
        f"{data['body_intro']}\n\n"
        f"Template: {data['template_key']}\n"
        f"Generated: {data['created_at']}\n"
    )

    attachment_path = Path(data["document_path"])
    attachment_bytes = attachment_path.read_bytes()
    msg.add_attachment(
        attachment_bytes,
        maintype="text",
        subtype="plain",
        filename=attachment_path.name,
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        if use_tls:
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)

    data["sent"] = True
    data["sent_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    result = {"approval_id": approval_id, "sent": True, "sent_at": data["sent_at"]}
    write_legal_audit("sent", approval_id, result)
    return result
