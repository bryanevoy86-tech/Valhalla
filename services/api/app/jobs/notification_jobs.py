"""
Notification dispatch job - process queued webhooks and emails.
"""

import json
import smtplib
import ssl
import datetime as dt
import httpx
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.settings import settings
from app.models.notify import Outbox


def _send_email(row: Outbox) -> None:
    """Send email using SMTP settings."""
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASS and settings.SMTP_FROM):
        raise RuntimeError("SMTP not configured")
    
    context = ssl.create_default_context()
    msg = f"From: {settings.SMTP_FROM}\r\nTo: {row.target}\r\nSubject: {row.subject or ''}\r\n\r\n{row.payload_json or ''}"
    
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.sendmail(settings.SMTP_FROM, [row.target], msg.encode("utf-8"))


def dispatch_pending(limit: int = 20) -> dict:
    """Process queued outbox items; returns counts."""
    db: Session = SessionLocal()
    sent = 0
    errored = 0
    
    try:
        rows = (
            db.query(Outbox)
            .filter(Outbox.status == "queued")
            .order_by(Outbox.id.asc())
            .limit(limit)
            .all()
        )
        
        # Sync client for webhooks
        with httpx.Client(timeout=10) as client:
            for r in rows:
                try:
                    if r.kind == "webhook":
                        resp = client.post(
                            r.target,
                            json=json.loads(r.payload_json or "{}")
                        )
                        resp.raise_for_status()
                    elif r.kind == "email":
                        _send_email(r)
                    else:
                        raise RuntimeError("unknown outbox kind")
                    
                    r.status = "sent"
                    r.sent_at = dt.datetime.now(dt.timezone.utc)
                    sent += 1
                except Exception as e:
                    r.status = "error"
                    r.attempts = (r.attempts or 0) + 1
                    r.last_error = str(e)
                    errored += 1
            
            if sent or errored:
                db.commit()
        
        return {"ok": True, "sent": sent, "error": errored}
    finally:
        db.close()
