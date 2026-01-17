from __future__ import annotations
from typing import Any, Dict, List
from . import store

def _annualize(amount: float, cadence: str) -> float:
    c = (cadence or "monthly").lower()
    if c == "weekly":
        return amount * 52
    if c == "biweekly":
        return amount * 26
    if c == "quarterly":
        return amount * 4
    if c == "yearly":
        return amount
    # monthly default
    return amount * 12

def audit() -> Dict[str, Any]:
    items = store.list_items()
    active = [x for x in items if x.get("status") == "active"]
    by_name = {}
    for s in active:
        key = (s.get("name") or "").strip().lower()
        by_name.setdefault(key, []).append(s)

    duplicates = [v for v in by_name.values() if len(v) > 1]
    annual_total = 0.0
    for s in active:
        annual_total += _annualize(float(s.get("amount") or 0.0), str(s.get("cadence") or "monthly"))

    return {
        "active_count": len(active),
        "duplicates": duplicates,
        "annualized_total": round(annual_total, 2),
    }
