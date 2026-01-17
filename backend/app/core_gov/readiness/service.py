"""
P-READINESS-1: Readiness service checking system health.

Verifies that core modules are initialized and ready:
- budget_obligations
- house_budget
- accounts
- ledger
- followups
"""
from typing import Dict, Any


def readiness() -> Dict[str, Any]:
    """
    Check readiness status of all core modules.
    
    Returns:
        dict with keys:
            - ready (bool): True if all checks pass
            - budget_obligations (bool)
            - house_budget (bool)
            - accounts (bool)
            - ledger (bool)
            - followups (bool)
            - message (str)
    """
    from backend.app.core_gov.budget_obligations.store import list_items as budget_obligations_list
    from backend.app.core_gov.house_budget.store import get as house_budget_get
    from backend.app.core_gov.accounts.store import list_items as accounts_list
    from backend.app.core_gov.ledger_light.store import list_items as ledger_list
    from backend.app.core_gov.followups.store import list_items as followups_list
    
    checks = {}
    
    try:
        budget_obligations_list()
        checks["budget_obligations"] = True
    except Exception:
        checks["budget_obligations"] = False
    
    try:
        house_budget_get()
        checks["house_budget"] = True
    except Exception:
        checks["house_budget"] = False
    
    try:
        accounts_list()
        checks["accounts"] = True
    except Exception:
        checks["accounts"] = False
    
    try:
        ledger_list()
        checks["ledger"] = True
    except Exception:
        checks["ledger"] = False
    
    try:
        followups_list()
        checks["followups"] = True
    except Exception:
        checks["followups"] = False
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        **checks,
        "message": "System ready" if all_ready else "Some modules not ready"
    }
