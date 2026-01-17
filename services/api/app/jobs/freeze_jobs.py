"""
Freeze jobs - checks for drawdown thresholds and risk management alerts.
"""

from ..core.config import settings


def check_drawdown(prev_balance: float, current_balance: float) -> dict:
    """
    Check if current balance has dropped below freeze threshold relative to previous balance.
    
    Formula: (prev_balance - current_balance) / prev_balance >= FREEZE_DRAWDOWN_PCT
    
    Args:
        prev_balance: Previous balance to compare against
        current_balance: Current balance to check
        
    Returns:
        dict with frozen (bool), drawdown_pct, threshold_pct, message
    """
    if prev_balance <= 0:
        return {
            "ok": True,
            "frozen": False,
            "drawdown_pct": 0.0,
            "threshold_pct": settings.FREEZE_DRAWDOWN_PCT,
            "message": "No previous balance to compare"
        }
    
    drawdown = (prev_balance - current_balance) / prev_balance
    threshold = settings.FREEZE_DRAWDOWN_PCT
    frozen = drawdown >= threshold
    
    return {
        "ok": True,
        "frozen": frozen,
        "drawdown_pct": round(drawdown, 4),
        "threshold_pct": threshold,
        "prev_balance": prev_balance,
        "current_balance": current_balance,
        "message": f"FREEZE TRIGGERED - {drawdown*100:.2f}% drawdown" if frozen else "Within acceptable drawdown"
    }
