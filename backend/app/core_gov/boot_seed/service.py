"""
P-BOOT-1: Boot seed service for system initialization.

Ensures minimum required data exists:
- system_config
- budget_categories
- house_budget
"""
from typing import Dict, Any


def seed_minimum() -> Dict[str, Any]:
    """
    Ensure minimum required system data exists.
    
    Returns:
        dict with keys:
            - success (bool)
            - system_config (dict)
            - budget_categories (dict)
            - house_budget (dict)
            - message (str)
    """
    result = {
        "success": True,
        "system_config": {},
        "budget_categories": {},
        "house_budget": {},
        "message": "Seed complete"
    }
    
    # Ensure system_config exists
    try:
        from backend.app.core_gov.system_config.store import get, DEFAULT
        config = get()
        result["system_config"] = config
    except Exception:
        # Create default config
        try:
            from backend.app.core_gov.system_config.store import save, DEFAULT
            result["system_config"] = save({})
        except Exception as e:
            result["system_config"] = {"error": str(e)}
    
    # Ensure budget_categories exist
    try:
        from backend.app.core_gov.budget_categories.store import list_items
        categories = list_items()
        if not categories:
            from backend.app.core_gov.budget_categories.store import create
            create(name="Utilities", annual_budget=1200)
            create(name="Groceries", annual_budget=6000)
            categories = list_items()
        result["budget_categories"] = {"count": len(categories)}
    except Exception as e:
        result["budget_categories"] = {"error": str(e)}
    
    # Ensure house_budget exists
    try:
        from backend.app.core_gov.house_budget.store import get as hb_get
        budget = hb_get()
        result["house_budget"] = budget or {}
    except Exception:
        # Create default house budget
        try:
            from backend.app.core_gov.house_budget.store import save
            budget = {
                "monthly_income": 5000,
                "annual_reserve": 3000,
                "currency": "USD"
            }
            result["house_budget"] = save(budget)
        except Exception as e:
            result["house_budget"] = {"error": str(e)}
    
    return result
