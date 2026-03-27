from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List
from . import store

def _add_months(dt: datetime, months: int) -> datetime:
    # simple month add
    y = dt.year + (dt.month - 1 + months) // 12
    m = (dt.month - 1 + months) % 12 + 1
    d = min(dt.day, 28)
    return datetime(y, m, d)

def warranty_report(limit: int = 50) -> Dict[str, Any]:
    items = [x for x in store.list_items() if x.get("status") == "active"]
    rows = []
    for a in items:
        m = int(a.get("warranty_months") or 0)
        pd = a.get("purchase_date") or ""
        if m <= 0 or not pd:
            continue
        try:
            dt = datetime.fromisoformat(pd)
            exp = _add_months(dt, m).date().isoformat()
            rows.append({"id": a.get("id"), "name": a.get("name"), "purchase_date": pd, "expires": exp, "months": m})
        except Exception:
            continue
    rows.sort(key=lambda x: x.get("expires",""))
    return {"items": rows[:max(1, min(500, int(limit or 50)))]}
