"""
SMTP email sending utility using app.core.settings.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from app.core.settings import settings
from app.core.engines.dispatch_guard import guard_outreach


def send_email(subject: str, recipient_email: str, body: str, html: bool = False) -> Dict[str, str]:
    guard_outreach()
    msg = MIMEMultipart()
    msg['From'] = settings.SMTP_FROM or 'noreply@valhalla.local'
    msg['To'] = recipient_email
    msg['Subject'] = subject

    part = MIMEText(body, 'html' if html else 'plain')
    msg.attach(part)

    try:
        if not settings.SMTP_HOST:
            return {"status": "failure", "message": "SMTP not configured (SMTP_HOST missing)"}

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        if settings.SMTP_PORT == 587:
            server.starttls()
        if settings.SMTP_USER and settings.SMTP_PASS:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.sendmail(msg['From'], [recipient_email], msg.as_string())
        server.quit()
        return {"status": "success", "message": "Email sent"}
    except Exception as e:  # pragma: no cover
        return {"status": "failure", "message": str(e)}
