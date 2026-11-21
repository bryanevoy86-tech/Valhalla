"""Stripe payout boundary: never invent a provider payout or transit status.

A real payout must use a verified Stripe API response, durable idempotency key,
owner spending authority, and read-back. Those steps are NOT implemented here.
"""
from app.core.engines.actions import MONEY_MOVE
from app.core.engines.guard_runtime import enforce_engine
from app.core.runtime_flags import is_live


def payout_to_bank(amount_cents, account_id):
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
            "verified": False,
            "amount": amount_cents,
            "account": account_id,
        }
    # No provider call exists on this pathway; BLOCK real movement rather
    # than generating a fake po_* ID.
    raise RuntimeError("STRIPE_PAYOUT_PROVIDER_NOT_IMPLEMENTED")


def get_payout_status(payout_id):
    # No Stripe lookup takes place here. The only truthful status is unknown.
    return {
        "id": payout_id,
        "status": "unverified",
        "verified": False,
    }
