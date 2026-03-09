"""Stripe integration client."""
from app.core.runtime_flags import is_live


def create_payment_intent(amount_cents, currency="usd"):
    """Create a Stripe payment intent."""
    if not is_live():
        return {
            "id": "pi_sandbox",
            "status": "sandbox"
        }

    # REAL STRIPE SDK CALL HERE
    return {
        "id": "pi_live",
        "status": "requires_confirmation"
    }


def confirm_payment(payment_intent_id):
    """Confirm a payment intent."""
    if not is_live():
        return {"status": "sandbox", "confirmed": True}
    
    return {"status": "succeeded"}


def get_payment_status(payment_intent_id):
    """Get status of a payment intent."""
    return {
        "id": payment_intent_id,
        "status": "succeeded" if is_live() else "sandbox"
    }
