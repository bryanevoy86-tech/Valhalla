"""Deal to cash pipeline."""
from app.integrations.stripe.payouts import payout_to_bank
from app.integrations.quickbooks.sync import sync_revenue, sync_fees, sync_profit


def close_deal(amount_cents, net_after_fees=None):
    """
    Close a deal and move cash.
    
    Flow:
    1. Calculate net amount (amount - fees)
    2. Sync revenue to QuickBooks
    3. Sync fees to QuickBooks
    4. Sync profit to QuickBooks
    5. Initiate payout
    """
    if net_after_fees is None:
        # Default 3% fee
        fees = int(amount_cents * 0.03)
        net_after_fees = amount_cents - fees
    else:
        fees = amount_cents - net_after_fees

    # Sync to accounting
    sync_revenue(amount_cents)
    sync_fees(fees)
    sync_profit(net_after_fees)
    
    # Initiate payout
    payout_result = payout_to_bank(
        amount_cents=net_after_fees,
        account_id="OPERATIONS"
    )
    
    return {
        "status": "closed",
        "gross": amount_cents,
        "fees": fees,
        "net": net_after_fees,
        "payout_id": payout_result.get("payout_id")
    }


def get_deal_cash_status(deal_id):
    """Get cash status for a deal."""
    return {
        "deal_id": deal_id,
        "cash_status": "pending"
    }
