from __future__ import annotations
from typing import Any, Dict, List
from .cost import estimate

def push() -> Dict[str, Any]:
    created = 0
    warnings: List[str] = []
    est = estimate(status="open")
    if (est.get("items") or 0) <= 0:
        return {"created": 0, "skipped": True, "reason": "no open items"}

    try:
        from backend.app.core_gov.reminders import service as rsvc  # type: ignore
        rsvc.create(
            title=f"Shopping list ready ({est.get('items')} items)",
            due_date="",
            kind="shopping",
            notes=f"estimated_total={est.get('estimated_total')} unknown_cost={est.get('unknown_cost_items')}",
        )
        created += 1
    except Exception as e:
        warnings.append(f"reminders unavailable: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings, "estimate": est}
