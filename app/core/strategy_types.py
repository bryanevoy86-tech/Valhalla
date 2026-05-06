"""
Strategy Types - Enum for real estate strategies

This module defines the strategies that Heimdall Intelligence tracks and learns from.
Includes launch strategies and designed-but-not-yet-active future strategies.

Usage:
    from app.core.strategy_types import StrategyType
    
    strategy = StrategyType.WHOLESALE
    print(strategy.value)  # "wholesale"
"""

from enum import Enum


class StrategyType(str, Enum):
    """
    Enumeration of real estate strategies.
    
    Launch Strategies (V1):
        - WHOLESALE: Buy below market, sell quickly, minimal rehab
        - HOLD: Buy, rehab, rent for cash flow
        - FLIP: Buy, rehab, sell for appreciation
        - PARTNERSHIP: Joint ventures with partners
    
    Future Strategies (Designed, Not Yet Activated):
        - COMMERCIAL: Commercial property strategies
        - CREATIVE_FINANCE: Owner financing, subject-to, lease options
        - ARBITRAGE: Geographic/market arbitrage
        - DEVELOPMENT: Development and new construction
        - SYNDICATION: Pooled investment structures
    """
    
    # Launch Strategies (V1)
    WHOLESALE = "wholesale"
    """Buy below market rate, add value through negotiation, sell quickly"""
    
    HOLD = "hold"
    """Buy and rehabilitate, hold for cash flow generation"""
    
    FLIP = "flip"
    """Buy at discount, renovate, sell for appreciation"""
    
    PARTNERSHIP = "partnership"
    """Joint ventures with partners or investors"""
    
    # Future Strategies (Designed, post-launch)
    COMMERCIAL = "commercial"
    """Commercial real estate (office, retail, industrial)"""
    
    CREATIVE_FINANCE = "creative_finance"
    """Creative financing (owner financing, subject-to, lease options)"""
    
    ARBITRAGE = "arbitrage"
    """Geographic or market arbitrage opportunities"""
    
    DEVELOPMENT = "development"
    """Development and new construction projects"""
    
    SYNDICATION = "syndication"
    """Syndicated investment pools and structures"""


# Profit margin thresholds for viability (post-rehab)
STRATEGY_PROFIT_THRESHOLDS = {
    StrategyType.WHOLESALE: 0.10,  # 10% minimum spread
    StrategyType.HOLD: None,  # Based on cap rate, not spread
    StrategyType.FLIP: 0.25,  # 25% minimum profit
    StrategyType.PARTNERSHIP: None,  # Negotiated per deal
    StrategyType.COMMERCIAL: None,  # Strategy pending
    StrategyType.CREATIVE_FINANCE: None,  # Strategy pending
    StrategyType.ARBITRAGE: 0.15,  # 15% minimum if geographic
    StrategyType.DEVELOPMENT: None,  # Strategy pending
    StrategyType.SYNDICATION: None,  # Strategy pending
}

# Minimum deal size by strategy
STRATEGY_MINIMUM_DEAL_SIZE = {
    StrategyType.WHOLESALE: 5000,  # $5k minimum profit
    StrategyType.HOLD: 50000,  # $50k minimum purchase
    StrategyType.FLIP: 20000,  # $20k minimum profit
    StrategyType.PARTNERSHIP: 50000,  # $50k minimum
    StrategyType.COMMERCIAL: None,  # TBD
    StrategyType.CREATIVE_FINANCE: None,  # TBD
    StrategyType.ARBITRAGE: 15000,  # $15k minimum profit
    StrategyType.DEVELOPMENT: None,  # TBD
    StrategyType.SYNDICATION: None,  # TBD
}

# Display-friendly names
STRATEGY_DISPLAY = {
    StrategyType.WHOLESALE: "Wholesale",
    StrategyType.HOLD: "Hold/Rental",
    StrategyType.FLIP: "Flip",
    StrategyType.PARTNERSHIP: "Partnership",
    StrategyType.COMMERCIAL: "Commercial",
    StrategyType.CREATIVE_FINANCE: "Creative Finance",
    StrategyType.ARBITRAGE: "Arbitrage",
    StrategyType.DEVELOPMENT: "Development",
    StrategyType.SYNDICATION: "Syndication",
}

# Descriptions
STRATEGY_DESCRIPTION = {
    StrategyType.WHOLESALE: (
        "Purchase below market value and assign or quickly resell. "
        "Minimal holding time, quick capital turnover."
    ),
    StrategyType.HOLD: (
        "Purchase property, rehabilitate if needed, rent for monthly cash flow. "
        "Long-term wealth building strategy."
    ),
    StrategyType.FLIP: (
        "Purchase property, significantly rehabilitate, resell for appreciation. "
        "3-12 month project timeline."
    ),
    StrategyType.PARTNERSHIP: (
        "Joint ventures with partners or investors. "
        "Shared risk and reward structures."
    ),
    StrategyType.COMMERCIAL: (
        "Commercial real estate strategies (office, retail, industrial). "
        "[Designed for future implementation]"
    ),
    StrategyType.CREATIVE_FINANCE: (
        "Non-traditional financing strategies (owner carry, subject-to, lease-options). "
        "[Designed for future implementation]"
    ),
    StrategyType.ARBITRAGE: (
        "Geographic or market arbitrage. Buy low in one market, sell high in another. "
        "[Designed for future implementation]"
    ),
    StrategyType.DEVELOPMENT: (
        "Land development and new construction projects. "
        "[Designed for future implementation]"
    ),
    StrategyType.SYNDICATION: (
        "Syndicated investment pooling and structures. "
        "[Designed for future implementation]"
    ),
}

# Launch status
STRATEGY_STATUS = {
    StrategyType.WHOLESALE: "launch",
    StrategyType.HOLD: "launch",
    StrategyType.FLIP: "launch",
    StrategyType.PARTNERSHIP: "launch",
    StrategyType.COMMERCIAL: "designed",
    StrategyType.CREATIVE_FINANCE: "designed",
    StrategyType.ARBITRAGE: "designed",
    StrategyType.DEVELOPMENT: "designed",
    StrategyType.SYNDICATION: "designed",
}

# Grouped by status
STRATEGY_CATEGORIES = {
    "Launch (V1)": [
        StrategyType.WHOLESALE,
        StrategyType.HOLD,
        StrategyType.FLIP,
        StrategyType.PARTNERSHIP,
    ],
    "Future (Designed)": [
        StrategyType.COMMERCIAL,
        StrategyType.CREATIVE_FINANCE,
        StrategyType.ARBITRAGE,
        StrategyType.DEVELOPMENT,
        StrategyType.SYNDICATION,
    ],
}


def get_launch_strategies() -> list:
    """Return strategies available for launch (V1)"""
    return [
        StrategyType.WHOLESALE,
        StrategyType.HOLD,
        StrategyType.FLIP,
        StrategyType.PARTNERSHIP,
    ]


def get_future_strategies() -> list:
    """Return strategies designed but not yet activated"""
    return [
        StrategyType.COMMERCIAL,
        StrategyType.CREATIVE_FINANCE,
        StrategyType.ARBITRAGE,
        StrategyType.DEVELOPMENT,
        StrategyType.SYNDICATION,
    ]


def get_all_strategies() -> list:
    """Return all strategies (launch + future)"""
    return get_launch_strategies() + get_future_strategies()


def get_strategy_profit_requirement(strategy: str) -> float or None:
    """
    Get the minimum profit threshold for a strategy.
    
    Args:
        strategy: Strategy code (e.g., "wholesale")
        
    Returns:
        Minimum profit threshold as decimal (e.g., 0.15 for 15%) or None if not set
    """
    try:
        strategy_enum = StrategyType(strategy.lower())
        return STRATEGY_PROFIT_THRESHOLDS.get(strategy_enum)
    except (ValueError, KeyError):
        return None
