from __future__ import annotations
from typing import Any, Dict, List
from . import store

def add_comp(prop_id: str, address: str, sold_price: float, sold_date: str = "", sqft: int = 0, notes: str = "") -> Dict[str, Any]:
    items = store.list_items()
    p = next((x for x in items if x.get("id") == prop_id), None)
    if not p:
        raise KeyError("not found")
    intel = p.get("intel") or {}
    comps = intel.get("comps") or []
    comps.append({
        "address": address,
        "sold_price": float(sold_price or 0.0),
        "sold_date": sold_date or "",
        "sqft": int(sqft or 0),
        "notes": notes or "",
    })
    intel["comps"] = comps
    p["intel"] = intel
    store.save_items(items)
    return {"prop_id": prop_id, "count": len(comps)}

def comps_summary(prop_id: str) -> Dict[str, Any]:
    items = store.list_items()
    p = next((x for x in items if x.get("id") == prop_id), None)
    if not p:
        raise KeyError("not found")
    comps = ((p.get("intel") or {}).get("comps") or [])
    prices = [float(c.get("sold_price") or 0.0) for c in comps if (c.get("sold_price") or 0)]
    avg = round(sum(prices)/len(prices), 2) if prices else 0.0
    return {"prop_id": prop_id, "comps": len(comps), "avg_sold_price": avg}
