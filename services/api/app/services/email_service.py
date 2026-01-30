"""
Email service for sending system emails.

This service integrates the system identity (VALHALLA_SYSTEM_EMAIL)
with the existing SMTP configuration in settings to send emails from
the system account.

It provides methods for:
    - send_email: Send a basic email
    - send_summary: Send a summary email to the default recipient
    - build_from_header: Build a properly formatted From header
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.core.identity import system_identity, get_system_email


def build_from_header(identity: Optional[Dict[str, str]] = None) -> str:
    """
    Build a properly formatted From header.

    Args:
        identity: System identity dict. If None, fetches from system_identity().

    Returns:
        str: Formatted From header like "Valhalla Legacy Inc <email@example.com>"
    """
    if identity is None:
        identity = system_identity()

    from_name = identity["from_name"]
    email = identity["email"]

    return f"{from_name} <{email}>"


def send_email(
    to_email: str,
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    settings: Optional[Settings] = None,
    identity: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Send an email from the system account.

    Uses SMTP configuration from settings and system identity from environment.

    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
        settings: Settings object with SMTP configuration. If None, creates new Settings().
        identity: System identity dict. If None, fetches from system_identity().

    Returns:
        bool: True if email was sent successfully, False otherwise

    Raises:
        RuntimeError: If system email is not configured
    """
    try:
        if settings is None:
            settings = Settings()

        if identity is None:
            identity = system_identity()

        # Validate SMTP configuration
        if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASS:
            print("EMAIL CONFIG ERROR: Missing SMTP settings",
                  {"host": bool(settings.SMTP_HOST), "user": bool(settings.SMTP_USER), "pass": bool(settings.SMTP_PASS)},
                  flush=True)
            return False

        from_header = build_from_header(identity)
        system_email = identity["email"]

        # Create message (force UTF-8 so symbols like ✓ ⚠ ═ render + send correctly)
        if html_body:
            msg = MIMEMultipart("alternative")
        else:
            msg = MIMEText(body, "plain", "utf-8")

        msg["Subject"] = subject
        msg["From"] = from_header
        msg["To"] = to_email

        if html_body:
            msg.attach(MIMEText(body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Send via SMTP
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.sendmail(system_email, [to_email], msg.as_string())

        return True

    except Exception as e:
        import traceback
        print("EMAIL SEND ERROR:", repr(e), flush=True)
        print(traceback.format_exc(), flush=True)
        return False


def send_summary(
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    to_email: Optional[str] = None,
    settings: Optional[Settings] = None,
) -> bool:
    """
    Send a summary email to the default recipient (system email).

    This is used for daily summaries, status reports, etc. that should
    go to the system account's inbox.

    Args:
        subject: Email subject
        body: Plain text email body
        html_body: Optional HTML email body
        to_email: Override recipient. Defaults to system email.
        settings: Settings object with SMTP configuration.

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if to_email is None:
        to_email = get_system_email()

    return send_email(
        to_email=to_email,
        subject=subject,
        body=body,
        html_body=html_body,
        settings=settings,
    )
