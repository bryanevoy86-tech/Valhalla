from __future__ import annotations
from typing import Any, Dict, List
from .service import forecast_days_left

def rollup(limit: int = 20, window_days: int = 30) -> Dict[str, Any]:
    try:
        from backend.app.core_gov.inventory import store as istore  # type: ignore
        items = [x for x in istore.list_items() if x.get("status") == "active"]
    except Exception:
        items = []
    out = []
    for it in items:
        f = forecast_days_left(inv_item=it, window_days=window_days)
        if f.get("days_left") is not None:
            out.append({"id": it.get("id"), "name": it.get("name"), "location": it.get("location"), "days_left": f.get("days_left"), "qty_now": f.get("qty_now"), "per_day": f.get("per_day")})
    out.sort(key=lambda x: (x.get("days_left") if x.get("days_left") is not None else 999999))
    return {"items": out[:max(1, min(500, int(limit or 20)))]}
