from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _parse_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _days_since(dt: Optional[datetime]) -> Optional[int]:
    if not dt:
        return None
    now = datetime.now(timezone.utc)
    d = now - dt
    return int(d.total_seconds() // 86400)


def suggest_reorders(location: str = "", priority: str = "", tag: str = "", max_items: int = 25) -> Dict[str, Any]:
    items = store.list_items()
    if location:
        items = [x for x in items if x.get("location") == location]
    if priority:
        items = [x for x in items if x.get("priority") == priority]
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]

    suggestions: List[Dict[str, Any]] = []
    total_est_cost = 0.0

    for it in items:
        on_hand = float(it.get("on_hand") or 0)
        min_th = float(it.get("min_threshold") or 0)
        rq = float(it.get("reorder_qty") or 0)
        cad = int(it.get("cadence_days") or 0)
        unit_cost = float(it.get("est_unit_cost") or 0.0)

        last_p = _parse_dt(it.get("last_purchased") or "")
        days = _days_since(last_p)

        reasons = []
        if on_hand <= min_th and (min_th > 0 or on_hand <= 0):
            reasons.append("below_threshold")
        if cad > 0 and days is not None and days >= cad:
            reasons.append("cadence_due")

        if not reasons:
            continue

        qty = rq if rq > 0 else max(0.0, (min_th * 2) - on_hand)  # fallback heuristic
        est = float(qty) * float(unit_cost) if unit_cost > 0 else 0.0
        total_est_cost += est

        suggestions.append({
            "item_id": it.get("id"),
            "name": it.get("name"),
            "location": it.get("location"),
            "priority": it.get("priority"),
            "on_hand": on_hand,
            "min_threshold": min_th,
            "reorder_qty": qty,
            "unit": it.get("unit"),
            "preferred_brand": it.get("preferred_brand",""),
            "preferred_store": it.get("preferred_store",""),
            "reasons": reasons,
            "days_since_last_purchased": days,
            "est_unit_cost": unit_cost,
            "est_total_cost": est,
            "tags": it.get("tags") or [],
        })

    # sort: critical/high first, then estimated cost desc
    pr_rank = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    suggestions.sort(key=lambda x: (pr_rank.get(x.get("priority","normal"), 2), -float(x.get("est_total_cost") or 0.0)))

    return {
        "count": len(suggestions),
        "total_est_cost": float(total_est_cost),
        "items": suggestions[: int(max_items or 25)],
    }
