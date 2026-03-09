from __future__ import annotations
from typing import Any, Dict
from . import store

def set_arv(prop_id: str, arv: float, notes: str = "") -> Dict[str, Any]:
    items = store.list_items()
    p = next((x for x in items if x.get("id") == prop_id), None)
    if not p:
        raise KeyError("not found")
    intel = p.get("intel") or {}
    intel["arv"] = float(arv or 0.0)
    intel["arv_notes"] = notes or ""
    p["intel"] = intel
    store.save_items(items)
    return {"prop_id": prop_id, "arv": intel["arv"]}
