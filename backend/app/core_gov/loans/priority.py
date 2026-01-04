from __future__ import annotations
from typing import Any, Dict
from . import store

def score(l: Dict[str, Any]) -> int:
    s = 0
    amt = float(l.get("max_amount") or 0.0)
    if amt >= 250000: s += 20
    elif amt >= 50000: s += 10
    rate = float(l.get("rate_est") or 0.0)
    if rate and rate <= 10: s += 10
    if (l.get("status") or "") == "open": s += 5
    if (l.get("requires_personal_guarantee") is False): s += 5
    return max(0, min(100, s))

def rank(limit: int = 25) -> Dict[str, Any]:
    items = store.list_items()
    rows = []
    for x in items:
        x2 = dict(x)
        x2["priority_v1"] = score(x)
        rows.append(x2)
    rows.sort(key=lambda x: x.get("priority_v1", 0), reverse=True)
    return {"items": rows[:max(1, min(2000, int(limit or 25)))]}
