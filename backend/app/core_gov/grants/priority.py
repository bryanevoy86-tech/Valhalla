from __future__ import annotations
from typing import Any, Dict
from . import store

def score(g: Dict[str, Any]) -> int:
    s = 0
    amt = float(g.get("amount") or 0.0)
    if amt >= 50000: s += 20
    elif amt >= 10000: s += 10
    if (g.get("deadline") or ""): s += 10
    if (g.get("status") or "") == "open": s += 5
    return max(0, min(100, s))

def rank(limit: int = 25) -> Dict[str, Any]:
    items = store.list_items()
    rows = []
    for g in items:
        g2 = dict(g)
        g2["priority_v1"] = score(g)
        rows.append(g2)
    rows.sort(key=lambda x: x.get("priority_v1", 0), reverse=True)
    return {"items": rows[:max(1, min(2000, int(limit or 25)))]}
