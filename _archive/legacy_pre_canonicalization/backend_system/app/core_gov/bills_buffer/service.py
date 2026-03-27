from __future__ import annotations

from typing import Any, Dict, List

def required_buffer(days: int = 30) -> Dict[str, Any]:
    warnings: List[str] = []
    try:
        from backend.app.core_gov.budget_calendar import service as calsvc  # type: ignore
        cal = calsvc.project(days_ahead=int(days or 30))
    except Exception as e:
        return {"required": 0.0, "items": [], "warnings": [f"budget_calendar unavailable: {type(e).__name__}: {e}"]}

    items = cal.get("items") or []
    total = sum(float(x.get("amount") or 0.0) for x in items)
    return {"days": int(days or 30), "required": float(total), "items": items, "warnings": warnings}
