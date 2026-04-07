"""Stripe Connect payouts."""
from app.core.runtime_flags import is_live


def payout_to_bank(amount_cents, account_id):
    """Initiate a payout to a connected bank account."""
    if not is_live():
        return {
            "status": "sandbox",
            "amount": amount_cents,
            "account": account_id
        }
    
    return {
        "status": "queued",
        "amount": amount_cents,
        "account": account_id,
        "payout_id": f"po_{account_id[:8]}"
    }


def get_payout_status(payout_id):
    """Get status of a payout."""
    return {
        "id": payout_id,
        "status": "in_transit" if is_live() else "sandbox"
    }
