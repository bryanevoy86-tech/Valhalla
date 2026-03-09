"""
SANDBOX-safe test email endpoint.

Allows testing SMTP configuration without enabling real-world outreach effects.
Only sends to whitelisted internal recipients (DAILY_OPS_RECIPIENT_EMAIL or ALERT_RECIPIENT_EMAIL).
Requires X-API-Key authentication (builder key).
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from app.core.settings import settings
from app.services.email_service import send_email

router = APIRouter(prefix="/api/notify", tags=["notify"])


class TestEmailIn(BaseModel):
    subject: str
    body_text: str


@router.post("/test-email")
def send_test_email(
    payload: TestEmailIn,
    x_api_key: str = Header(None, alias="X-API-Key"),
):
    """
    Send a test email to internal recipient (SANDBOX-safe).
    
    Only works in SANDBOX mode. Sends to DAILY_OPS_RECIPIENT_EMAIL or ALERT_RECIPIENT_EMAIL.
    Requires X-API-Key (builder key) authentication.
    
    Returns:
        {"ok": true, "sent_to": recipient}
    """
    # Authenticate
    if not settings.BUILDER_KEY:
        raise HTTPException(status_code=503, detail="Builder key not configured")
    if not x_api_key or x_api_key != settings.BUILDER_KEY:
        raise HTTPException(status_code=401, detail="Invalid X-API-Key")

    # SANDBOX only
    app_env = (settings.APP_ENV or "").lower()
    if app_env not in {"sandbox", "dev"}:
        raise HTTPException(
            status_code=409,
            detail="Test email endpoint allowed only in SANDBOX/DEV environments"
        )

    # Get whitelisted recipient
    to_email = settings.DAILY_OPS_RECIPIENT_EMAIL or settings.ALERT_RECIPIENT_EMAIL
    if not to_email:
        raise HTTPException(
            status_code=500,
            detail="No internal recipient configured (DAILY_OPS_RECIPIENT_EMAIL or ALERT_RECIPIENT_EMAIL)"
        )

    # Send email
    success = send_email(
        to_email=to_email,
        subject=f"[SANDBOX TEST] {payload.subject}",
        body=payload.body_text,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Email send failed (check SMTP configuration)"
        )

    return {"ok": True, "sent_to": to_email}
