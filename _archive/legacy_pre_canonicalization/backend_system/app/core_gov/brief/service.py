"""
P-BRIEF-1: Brief service aggregating key information.

Builds a brief containing:
- mode (soft_launch, budget, etc.)
- bills_upcoming (next 7 days)
- followups_open (open followups)
- cash_plan (current cash position)
"""
from typing import Dict, Any


def build() -> Dict[str, Any]:
    """
    Build a brief aggregating key information.
    
    Returns:
        dict with keys:
            - mode (str)
            - bills_upcoming (list)
            - followups_open (list)
            - cash_plan (dict)
            - timestamp (str)
    """
    from datetime import datetime
    
    result = {
        "mode": "unknown",
        "bills_upcoming": [],
        "followups_open": [],
        "cash_plan": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Get mode from system config
    try:
        from backend.app.core_gov.system_config.store import get as config_get
        config = config_get()
        result["mode"] = config.get("soft_launch", False) and "soft_launch" or "budget"
    except Exception:
        result["mode"] = "unknown"
    
    # Get upcoming bills
    try:
        from backend.app.core_gov.budget_obligations.service import followups
        bills = followups(days_bills=7)
        result["bills_upcoming"] = bills.get("items", [])[:5]
    except Exception:
        result["bills_upcoming"] = []
    
    # Get open followups
    try:
        from backend.app.core_gov.followups.service import list_open
        result["followups_open"] = list_open()[:5]
    except Exception:
        result["followups_open"] = []
    
    # Get cash plan
    try:
        from backend.app.core_gov.house_budget.service import cash_plan_for_period
        result["cash_plan"] = cash_plan_for_period(days=7)
    except Exception:
        result["cash_plan"] = {}
    
    return result
