"""Fee calculation engine."""

# Standard arbitrage fee rate (3% for operations)
ARB_FEE_RATE = 0.03

# Alternative fee structures
FEE_STRUCTURES = {
    "standard": 0.03,      # 3%
    "premium": 0.05,       # 5%
    "discount": 0.01,      # 1%
}


def calculate_fee(gross_cents, fee_rate=ARB_FEE_RATE):
    """Calculate fee on gross amount."""
    return int(gross_cents * fee_rate)


def calculate_net(gross_cents, fee_rate=ARB_FEE_RATE):
    """Calculate net amount after fees."""
    fee = calculate_fee(gross_cents, fee_rate)
    return gross_cents - fee


def get_fee_breakdown(gross_cents, fee_rate=ARB_FEE_RATE):
    """Get detailed fee breakdown."""
    fee = calculate_fee(gross_cents, fee_rate)
    net = gross_cents - fee
    
    return {
        "gross": gross_cents,
        "fee": fee,
        "fee_rate": fee_rate,
        "net": net,
        "fee_percentage": fee_rate * 100
    }


def calculate_with_structure(gross_cents, structure="standard"):
    """Calculate fee using named structure."""
    fee_rate = FEE_STRUCTURES.get(structure, ARB_FEE_RATE)
    return get_fee_breakdown(gross_cents, fee_rate)
