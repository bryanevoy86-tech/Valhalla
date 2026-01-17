"""
Twilio SMS sending utility using app.core.settings.
"""
from typing import Dict
from app.core.settings import settings
from app.core.engines.dispatch_guard import guard_outreach


def send_sms(recipient_phone: str, message: str) -> Dict[str, str]:
    guard_outreach()
    try:
        if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE_NUMBER):
            return {"status": "failure", "message": "Twilio not configured (missing env vars)"}

        try:
            from twilio.rest import Client  # type: ignore
        except Exception as e:
            return {"status": "failure", "message": f"Twilio SDK not installed: {e}"}

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        _ = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=recipient_phone
        )
        return {"status": "success", "message": "SMS sent"}
    except Exception as e:  # pragma: no cover
        return {"status": "failure", "message": str(e)}
