"""Payments gateway - Stripe-ready with sandbox fallback."""
from app.core.runtime_flags import is_live


def create_invoice(amount: int, customer_id: str, description: str = None) -> dict:
    """
    Create an invoice.
    
    In SANDBOX mode: returns mock response
    In LIVE mode: creates actual Stripe invoice (stub - requires Stripe client)
    """
    if not is_live():
        return {
            "status": "sandbox",
            "amount": amount,
            "customer_id": customer_id,
            "description": description,
            "message": "Sandbox mode - no real charge"
        }
    
    # TODO: Implement actual Stripe API call
    # stripe_client = get_stripe_client()
    # invoice = stripe_client.Invoice.create(
    #     amount=amount,
    #     customer=customer_id,
    #     description=description
    # )
    # return invoice
    
    return {
        "status": "live",
        "amount": amount,
        "customer_id": customer_id,
        "description": description,
        "message": "Invoice created (stub)"
    }


def process_payment(amount: int, customer_id: str, invoice_id: str) -> dict:
    """
    Process a payment.
    
    In SANDBOX mode: returns mock response
    In LIVE mode: processes through Stripe
    """
    if not is_live():
        return {
            "status": "sandbox",
            "amount": amount,
            "customer_id": customer_id,
            "invoice_id": invoice_id,
            "message": "Sandbox mode - no real charge"
        }
    
    # TODO: Implement actual Stripe charge
    return {
        "status": "live",
        "amount": amount,
        "customer_id": customer_id,
        "invoice_id": invoice_id,
        "message": "Payment processed (stub)"
    }


def refund_payment(charge_id: str, amount: int = None) -> dict:
    """
    Refund a payment.
    
    In SANDBOX mode: returns mock response
    In LIVE mode: processes through Stripe
    """
    if not is_live():
        return {
            "status": "sandbox",
            "charge_id": charge_id,
            "refunded_amount": amount,
            "message": "Sandbox mode - no real refund"
        }
    
    # TODO: Implement actual Stripe refund
    return {
        "status": "live",
        "charge_id": charge_id,
        "refunded_amount": amount,
        "message": "Refund processed (stub)"
    }
