"""Profit split calculation."""
from app.fees.engine import calculate_fee


def split_profit(gross_cents, fee_rate=0.03):
    """
    Split profit between operations and net.
    
    Args:
        gross_cents: Total deal amount
        fee_rate: Fee rate (0.03 = 3%)
    
    Returns:
        dict with breakdown
    """
    fees = calculate_fee(gross_cents, fee_rate)
    net = gross_cents - fees
    
    return {
        "gross": gross_cents,
        "fees": fees,
        "net": net,
        "fee_rate": fee_rate,
        "status": "split"
    }


def split_three_way(gross_cents, operations_cut=0.03, partner_cut=None):
    """
    Split profit three ways: operations fee, partner share, net.
    
    Args:
        gross_cents: Total amount
        operations_cut: Operations fee rate (default 3%)
        partner_cut: Partner share (if applicable)
    
    Returns:
        dict with three-way split
    """
    ops_fees = calculate_fee(gross_cents, operations_cut)
    
    if partner_cut:
        partner_share = int(gross_cents * partner_cut)
        net = gross_cents - ops_fees - partner_share
    else:
        partner_share = 0
        net = gross_cents - ops_fees
    
    return {
        "gross": gross_cents,
        "operations": ops_fees,
        "partner": partner_share,
        "net": net
    }


def get_profit_split_summary(gross_cents, fee_rate=0.03):
    """Get profit split summary."""
    fees = calculate_fee(gross_cents, fee_rate)
    net = gross_cents - fees
    
    return {
        "gross_cents": gross_cents,
        "gross_dollars": gross_cents / 100,
        "fees_cents": fees,
        "fees_dollars": fees / 100,
        "net_cents": net,
        "net_dollars": net / 100,
        "fee_percentage": fee_rate * 100
    }
