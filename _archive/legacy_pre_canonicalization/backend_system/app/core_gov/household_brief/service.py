from __future__ import annotations
from typing import Any, Dict, List

def build(days_bills: int = 14) -> Dict[str, Any]:
    out: Dict[str, Any] = {"bills_upcoming": {}, "followups_open": [], "shopping_open": [], "notes": []}

    try:
        from backend.app.core_gov.budget_obligations.due import upcoming  # type: ignore
        out["bills_upcoming"] = upcoming(days=days_bills)
    except Exception as e:
        out["notes"].append(f"bills upcoming unavailable: {type(e).__name__}")

    try:
        from backend.app.followups import store as fstore  # type: ignore
        if hasattr(fstore, "list_followups"):
            out["followups_open"] = fstore.list_followups(status="open")[:50]
        else:
            out["followups_open"] = []
    except Exception as e:
        out["notes"].append(f"followups unavailable: {type(e).__name__}")

    try:
        from backend.app.core_gov.shopping_list import service as ssvc  # type: ignore
        out["shopping_open"] = ssvc.list_items(status="open")[:25]
    except Exception:
        out["shopping_open"] = []

    return out
