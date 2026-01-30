"""
Test Email Router - Send test notifications to verify email service is working.
"""

from fastapi import APIRouter
from app.core.identity import system_identity
from app.services.email_service import send_email

router = APIRouter(prefix="/api/notify", tags=["notify"])


@router.post("/test-email")
def test_email():
    """
    Send a test email from the system account.
    
    This endpoint verifies that:
    1. System identity is configured (VALHALLA_SYSTEM_EMAIL)
    2. Email service can send messages
    3. Notification channel is online
    
    Returns:
        dict: Status of the test email send
    """
    identity = system_identity()
    to_email = identity["email"]

    send_email(
        to_email=to_email,
        subject="Heimdall: Notification channel online ✅",
        body="If you received this, Valhalla can send operational emails from Render."
    )
    
    return {
        "ok": True,
        "sent_to": to_email,
        "subject": "Heimdall: Notification channel online ✅"
    }
