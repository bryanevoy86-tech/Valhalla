from __future__ import annotations
from typing import Any, Dict, List

def list_for_month(month: str) -> List[Dict[str, Any]]:
    try:
        from backend.app.core_gov.ledger_light import store as lstore
        items = lstore.list_items()
    except Exception:
        items = []
    out = []
    for x in items:
        d = (x.get("date") or "")
        if d.startswith(month):
            out.append(x)
    out.sort(key=lambda r: r.get("date",""))
    return out[:50000]
