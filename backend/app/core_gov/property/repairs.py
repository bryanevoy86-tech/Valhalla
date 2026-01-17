from __future__ import annotations
from typing import Any, Dict
from . import store

def add_repair(prop_id: str, item: str, cost: float, notes: str = "") -> Dict[str, Any]:
    items = store.list_items()
    p = next((x for x in items if x.get("id") == prop_id), None)
    if not p:
        raise KeyError("not found")
    intel = p.get("intel") or {}
    repairs = intel.get("repairs") or []
    repairs.append({"item": item, "cost": float(cost or 0.0), "notes": notes or ""})
    intel["repairs"] = repairs
    intel["repairs_total"] = round(sum(float(r.get("cost") or 0.0) for r in repairs), 2)
    p["intel"] = intel
    store.save_items(items)
    return {"prop_id": prop_id, "repairs": len(repairs), "repairs_total": intel["repairs_total"]}
