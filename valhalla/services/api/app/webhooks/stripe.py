"""
Module 36: Stripe Webhook Handler
Handles incoming webhook events from Stripe.
"""
from fastapi import APIRouter, Request
from app.heimdall.authority import is_live

router = APIRouter(prefix="/webhooks/stripe")


@router.post("")
async def stripe_webhook(req: Request):
    """
    Handle Stripe webhook events.
    
    Supported events:
    - payment_intent.succeeded: Payment completed
    - payment_intent.payment_failed: Payment failed
    - charge.refunded: Refund processed
    """
    if not is_live():
        return {"status": "sandbox_ignored"}
    
    try:
        payload = await req.json()
        event_type = payload.get("type")

        if event_type == "payment_intent.succeeded":
            # Log payment success
            intent_id = payload.get("data", {}).get("object", {}).get("id")
            return {
                "status": "payment_recorded",
                "intent_id": intent_id,
                "event": "payment_intent.succeeded"
            }

        elif event_type == "payment_intent.payment_failed":
            # Log payment failure
            return {
                "status": "payment_failure_recorded",
                "event": "payment_intent.payment_failed"
            }

        elif event_type == "charge.refunded":
            # Log refund
            return {
                "status": "refund_recorded",
                "event": "charge.refunded"
            }

        return {
            "status": "ignored",
            "event": event_type
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
