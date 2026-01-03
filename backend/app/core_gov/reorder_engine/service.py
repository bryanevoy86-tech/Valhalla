from __future__ import annotations

from typing import Any, Dict, List

def build_reorder_list() -> Dict[str, Any]:
    warnings: List[str] = []
    try:
        from backend.app.core_gov.house_inventory import service as invsvc  # type: ignore
        low = invsvc.low_stock()
    except Exception as e:
        return {"items": [], "warnings": [f"house_inventory unavailable: {type(e).__name__}: {e}"]}

    items = []
    for x in low:
        items.append({
            "inventory_id": x.get("id",""),
            "name": x.get("name",""),
            "location": x.get("location",""),
            "qty": x.get("qty", 0.0),
            "min_qty": x.get("min_qty", 0.0),
            "unit": x.get("unit","each"),
            "priority": x.get("priority","normal"),
        })
    pr = {"high": 0, "normal": 1, "low": 2}
    items.sort(key=lambda x: (pr.get((x.get("priority") or "normal").lower(), 9), x.get("name","")))
    return {"items": items, "warnings": warnings}

def create_purchase_followups(days_ahead: int = 2) -> Dict[str, Any]:
    res = build_reorder_list()
    warnings = res.get("warnings") or []
    created = 0
    try:
        from datetime import date, timedelta
        from backend.app.followups import store as fstore  # type: ignore
        due = (date.today() + timedelta(days=max(0, int(days_ahead or 2)))).isoformat()
        for it in res.get("items") or []:
            try:
                fstore.create_followup({
                    "type": "purchase",
                    "title": f"Buy: {it.get('name','')}",
                    "due_date": due,
                    "status": "open",
                    "meta": it,
                })
                created += 1
            except Exception:
                warnings.append("followups: create_followup missing/failed (safe)")
                break
    except Exception as e:
        warnings.append(f"followups unavailable: {type(e).__name__}: {e}")

    return {"created": created, "warnings": warnings, "items": res.get("items") or []}
