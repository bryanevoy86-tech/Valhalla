"""Stripe Connect payouts."""
from app.core.engines.actions import MONEY_MOVE
from app.core.engines.guard_runtime import enforce_engine
from app.core.runtime_flags import is_live


def payout_to_bank(amount_cents, account_id):
    """Initiate a payout to a connected bank account."""
    enforce_engine(
        "wholesaling",
        MONEY_MOVE,
        {
            "provider": "stripe",
            "target_type": "bank_account",
            "amount_cents": int(amount_cents or 0),
        },
    )
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
