from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List


def weekly_plan(days: int = 7) -> Dict[str, Any]:
    warnings: List[str] = []
    end = (date.today() + timedelta(days=int(days or 7))).isoformat()

    low = []
    try:
        from backend.app.core_gov.inventory import service as inv  # type: ignore
        for it in inv.list_items(status="active"):
            rp = float(it.get("reorder_point") or 0.0)
            if rp > 0 and float(it.get("qty") or 0.0) <= rp:
                low.append(it)
    except Exception as e:
        warnings.append(f"inventory unavailable: {type(e).__name__}: {e}")

    open_shop = []
    try:
        from backend.app.core_gov.shopping import service as ssvc  # type: ignore
        open_shop = ssvc.list_items(status="open")
    except Exception as e:
        warnings.append(f"shopping unavailable: {type(e).__name__}: {e}")

    bills = []
    try:
        from backend.app.core_gov.budget import calendar as cal  # type: ignore
        ev = cal.next_n_days_calendar(int(days or 7))
        bills = [x for x in (ev.get("items", []) if isinstance(ev, dict) else (ev or [])) if x.get("type") == "obligation"]
    except Exception as e:
        warnings.append(f"budget_calendar unavailable: {type(e).__name__}: {e}")

    # price hints
    price = {}
    try:
        from backend.app.core_gov.pricebook import service as pb  # type: ignore
        for p in pb.list_items(status="active"):
            price[(p.get("item_name") or "").strip().lower()] = p
    except Exception as e:
        warnings.append(f"pricebook unavailable: {type(e).__name__}: {e}")

    def _est(item_name: str, qty: float) -> float:
        p = price.get((item_name or "").strip().lower())
        if not p:
            return 0.0
        return float(p.get("typical_unit_price") or 0.0) * float(qty or 1.0)

    plan_items = []
    for it in low:
        name = (it.get("name") or "").strip()
        need = max(1.0, float(it.get("desired_qty") or 0.0) - float(it.get("qty") or 0.0))
        plan_items.append({
            "type": "reorder",
            "name": name,
            "qty": float(need),
            "unit": it.get("unit") or "each",
            "category": it.get("category") or "general",
            "est_cost": float(_est(name, need)),
            "store_hint": (price.get(name.lower(), {}) or {}).get("preferred_store",""),
        })

    for it in open_shop:
        name = (it.get("name") or "").strip()
        qty = float(it.get("qty") or 1.0)
        plan_items.append({
            "type": "shopping",
            "name": name,
            "qty": qty,
            "unit": it.get("unit") or "each",
            "category": it.get("category") or "general",
            "est_cost": float(it.get("est_unit_cost") or _est(name, qty)) * (qty if float(it.get("est_unit_cost") or 0.0) > 0 else 1.0),
            "store_hint": it.get("store_hint") or (price.get(name.lower(), {}) or {}).get("preferred_store",""),
        })

    total_est = sum(float(x.get("est_cost") or 0.0) for x in plan_items)

    return {
        "range_days": int(days or 7),
        "through": end,
        "items": plan_items[:200],
        "bills_due": bills[:50],
        "total_estimated_spend": float(total_est),
        "warnings": warnings,
        "note": "This is a planning view. Use Reorder scan to auto-create missing shopping items if desired.",
    }
