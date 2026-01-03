"""
P-DAILYOPS-1: Daily operations service.

Runs daily operations including:
- budget_obligations.followups
- shopping_list.ops (or fallback to followups)
"""
from typing import Dict, Any


def run(days_bills: int = 7) -> Dict[str, Any]:
    """
    Run daily operations.
    
    Args:
        days_bills: Number of days to look ahead for bills (default 7)
    
    Returns:
        dict with keys:
            - success (bool)
            - budget_obligations_followups (dict)
            - shopping_list_ops (dict)
            - message (str)
    """
    result = {
        "success": True,
        "budget_obligations_followups": {},
        "shopping_list_ops": {},
        "message": "Daily operations completed"
    }
    
    # Safe call: budget_obligations.followups
    try:
        from backend.app.core_gov.budget_obligations.service import followups as budget_obligations_followups
        result["budget_obligations_followups"] = budget_obligations_followups(days_bills=days_bills)
    except Exception as e:
        result["budget_obligations_followups"] = {"error": str(e)}
    
    # Safe call: shopping_list.ops or fallback to followups
    try:
        try:
            from backend.app.core_gov.shopping_list.service import ops as shopping_list_ops
            result["shopping_list_ops"] = shopping_list_ops()
        except (ImportError, AttributeError):
            # Fallback to followups
            from backend.app.core_gov.followups.service import list_open
            result["shopping_list_ops"] = {"items": list_open()}
    except Exception as e:
        result["shopping_list_ops"] = {"error": str(e)}
    
    return result
