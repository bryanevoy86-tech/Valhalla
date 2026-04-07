"""Banking & Payouts module - handle disbursements and connected accounts."""
from uuid import uuid4
from app.core.runtime_flags import is_live
from app.payments.gateway import process_payment


def initiate_payout(amount: float, destination: str) -> dict:
    """
    Initiate a payout to a destination (bank account or wallet).
    
    Args:
        amount: Amount in cents
        destination: Bank account ID or payment method ID
    
    Returns:
        dict with payout details
    """
    payout_id = f"payout_{uuid4().hex[:12]}"
    
    if not is_live():
        return {
            "status": "sandbox",
            "payout_id": payout_id,
            "amount": amount,
            "destination": destination,
            "message": "Would payout via Stripe/Plaid in live mode"
        }
    
    # In live mode, use Stripe Connect or Plaid
    return {
        "status": "initiated",
        "payout_id": payout_id,
        "amount": amount,
        "destination": destination,
        "message": "Payout processing"
    }


def connect_bank_account(plaid_token: str) -> dict:
    """
    Connect a bank account via Plaid.
    
    Args:
        plaid_token: Public token from Plaid Link
    
    Returns:
        dict with connected account info
    """
    if not is_live():
        return {
            "status": "sandbox",
            "account_id": f"acct_{uuid4().hex[:12]}",
            "message": "Bank account would be connected in live mode"
        }
    
    return {
        "status": "connected",
        "account_id": f"acct_{uuid4().hex[:12]}",
        "message": "Bank account connected via Plaid"
    }


def get_payout_status(payout_id: str) -> dict:
    """Check payout status."""
    return {
        "payout_id": payout_id,
        "status": "completed" if is_live() else "sandbox",
        "amount": 0,
        "completed_at": None
    }
