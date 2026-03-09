from __future__ import annotations
from typing import Any, Dict, List
from . import store

def estimate(status: str = "open") -> Dict[str, Any]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    total = 0.0
    unknown = 0
    for x in items:
        unit = float(x.get("est_unit_cost") or 0.0)
        qty = float(x.get("qty") or 0.0)
        if unit <= 0:
            unknown += 1
        total += unit * qty
    return {"status": status, "items": len(items), "unknown_cost_items": unknown, "estimated_total": round(total, 2)}
