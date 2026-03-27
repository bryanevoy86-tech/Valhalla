from __future__ import annotations
from typing import Any, Dict
from . import store

def set_rent(prop_id: str, projected_rent: float, notes: str = "") -> Dict[str, Any]:
    items = store.list_items()
    p = next((x for x in items if x.get("id") == prop_id), None)
    if not p:
        raise KeyError("not found")
    intel = p.get("intel") or {}
    intel["projected_rent"] = float(projected_rent or 0.0)
    intel["rent_notes"] = notes or ""
    p["intel"] = intel
    store.save_items(items)
    return {"prop_id": prop_id, "projected_rent": intel["projected_rent"]}
