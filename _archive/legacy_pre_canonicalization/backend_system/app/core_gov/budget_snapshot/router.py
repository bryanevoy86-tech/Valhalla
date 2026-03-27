from __future__ import annotations
from typing import Any, Dict

def snapshot(days: int = 14) -> Dict[str, Any]:
    out: Dict[str, Any] = {"obligations": [], "upcoming": {}, "house_budget": {}, "notes": []}
    try:
        from backend.app.core_gov.budget_obligations import service as obsvc
        out["obligations"] = obsvc.list_items(status="active")
    except Exception as e:
        out["notes"].append(f"obligations unavailable: {type(e).__name__}")
    try:
        from backend.app.core_gov.budget_obligations.due import upcoming
        out["upcoming"] = upcoming(days=days)
    except Exception as e:
        out["notes"].append(f"upcoming unavailable: {type(e).__name__}")
    try:
        from backend.app.core_gov.house_budget import store as hbstore
        out["house_budget"] = hbstore.get_profile()
    except Exception as e:
        out["notes"].append(f"house_budget unavailable: {type(e).__name__}")
    return out
