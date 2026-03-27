from ..services.mailer import send_email


def send_email_task(to: list[str], subject: str, text: str, html: str | None = None):
    # Lightweight wrapper for RQ
    send_email(to, subject, text, html)
    return {"ok": True, "to": to, "subject": subject}
