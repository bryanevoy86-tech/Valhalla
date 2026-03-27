from __future__ import annotations
from typing import Any, Dict
from . import store

def set_rating(prop_id: str, score: int, notes: str = "") -> Dict[str, Any]:
    items = store.list_items()
    p = next((x for x in items if x.get("id") == prop_id), None)
    if not p:
        raise KeyError("not found")
    s = max(0, min(100, int(score or 0)))
    intel = p.get("intel") or {}
    intel["neighborhood_score"] = s
    intel["neighborhood_notes"] = notes or ""
    p["intel"] = intel
    store.save_items(items)
    return {"prop_id": prop_id, "neighborhood_score": s}
