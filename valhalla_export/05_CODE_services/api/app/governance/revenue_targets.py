"""Revenue target enforcement - monthly revenue goals."""
from datetime import datetime

# Monthly revenue target in cents ($5M)
MONTHLY_TARGET = 5_000_000_00  # 5,000,000.00


def validate_monthly_revenue(actual_revenue: float) -> dict:
    """
    Validate actual monthly revenue against target.
    
    Args:
        actual_revenue: Actual revenue in cents
    
    Returns:
        dict with target, actual, variance, status
    """
    variance = actual_revenue - MONTHLY_TARGET
    variance_pct = (variance / MONTHLY_TARGET * 100) if MONTHLY_TARGET > 0 else 0
    
    status = "on_track" if variance >= 0 else "below_target"
    
    return {
        "month": datetime.utcnow().strftime("%Y-%m"),
        "target": MONTHLY_TARGET,
        "actual": actual_revenue,
        "variance": variance,
        "variance_pct": variance_pct,
        "status": status,
        "achievement_pct": (actual_revenue / MONTHLY_TARGET * 100) if MONTHLY_TARGET > 0 else 0
    }


def get_revenue_forecast(deals_pending: int, avg_deal_value: float) -> dict:
    """
    Forecast revenue based on pending deals.
    
    Args:
        deals_pending: Number of deals in pipeline
        avg_deal_value: Average deal value in cents
    
    Returns:
        dict with forecast
    """
    projected_revenue = deals_pending * avg_deal_value
    
    return {
        "deals_pending": deals_pending,
        "avg_deal_value": avg_deal_value,
        "projected_revenue": projected_revenue,
        "target": MONTHLY_TARGET,
        "gap": max(0, MONTHLY_TARGET - projected_revenue),
        "forecast": "on_track" if projected_revenue >= MONTHLY_TARGET else "shortfall"
    }


def check_monthly_compliance() -> dict:
    """Check if system should enforce revenue targets."""
    return {
        "enforcement_enabled": True,
        "monthly_target": MONTHLY_TARGET,
        "current_month": datetime.utcnow().strftime("%Y-%m"),
        "days_elapsed": datetime.utcnow().day,
        "days_remaining": 30 - datetime.utcnow().day
    }
