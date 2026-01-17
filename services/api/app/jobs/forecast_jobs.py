"""
Forecast jobs - financial projections based on current capital and expected yields.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from ..core.config import settings


def forecast_month_ahead(db: Session) -> dict:
    """
    Calculate projected balance one month ahead based on current capital and forecast yield.
    
    Formula: total_capital * (1 + FORECAST_MONTHLY_YIELD)
    
    Returns:
        dict with current_total, forecast_yield, projected_balance, currency
    """
    # Get total capital from capital_intake table
    try:
        total_capital = db.execute(
            text("SELECT COALESCE(SUM(amount), 0) FROM capital_intake WHERE currency = 'CAD'")
        ).scalar() or 0.0
    except Exception:
        total_capital = 0.0
    
    forecast_yield = settings.FORECAST_MONTHLY_YIELD
    projected_balance = float(total_capital) * (1 + forecast_yield)
    
    return {
        "ok": True,
        "current_total": float(total_capital),
        "forecast_yield": forecast_yield,
        "projected_balance": projected_balance,
        "currency": "CAD",
        "note": f"Projected balance one month ahead with {forecast_yield*100}% yield"
    }
