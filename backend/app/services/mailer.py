from __future__ import annotations

from collections.abc import Sequence

from ..core.config import get_settings


def send_email(to: Sequence[str], subject: str, text: str, html: str | None = None) -> None:
    s = get_settings()
    provider = (s.EMAIL_PROVIDER or "stub").lower()
    if provider == "sendgrid" and s.SENDGRID_API_KEY:
        _send_sendgrid(to, subject, text, html)
    else:
        _send_stub(to, subject, text, html)


def _send_stub(to, subject, text, html):
    print(f"[MAIL STUB] to={list(to)} subject={subject}\n{text}\n{html or ''}")


def _send_sendgrid(to, subject, text, html):
    import json
    import urllib.request

    s = get_settings()
    data = {
        "personalizations": [{"to": [{"email": addr} for addr in to]}],
        "from": {"email": s.EMAIL_FROM or "noreply@valhalla.local"},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text or ""},
            {"type": "text/html", "value": html or f"<pre>{text or ''}</pre>"},
        ],
    }
    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {s.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as _:
            pass
    except Exception as e:
        print(f"[MAIL SENDGRID ERR] {e}")
