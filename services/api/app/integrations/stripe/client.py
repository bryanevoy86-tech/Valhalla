"""Stripe integration client."""
from app.core.runtime_flags import is_live
from app.services.launch_readiness import require_channel_release


def create_payment_intent(amount_cents, currency="usd"):
    """Create a Stripe payment intent."""
    if not is_live():
        return {
            "id": "pi_sandbox",
            "status": "sandbox"
        }

    require_channel_release("commerce_and_fulfillment")
    raise RuntimeError("Live payment intent adapter unavailable")


def confirm_payment(payment_intent_id):
    """Confirm a payment intent."""
    if not is_live():
        return {"status": "sandbox", "confirmed": True}
    
    require_channel_release("commerce_and_fulfillment")
    raise RuntimeError("Live confirmation adapter unavailable")


def get_payment_status(payment_intent_id):
    """Get status of a payment intent."""
    return {
        "id": payment_intent_id,
        "status": "unverified" if is_live() else "sandbox"
    }
