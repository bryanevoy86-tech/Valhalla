from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create_comp(property_id: str, sold_price: float, sold_date: str, address: str, bed: Optional[int] = None, bath: Optional[float] = None, sqft: Optional[int] = None, distance_km: Optional[float] = None, notes: str = "") -> Dict[str, Any]:
    if not property_id or not sold_price:
        raise ValueError("property_id and sold_price required")
    
    items = store.list_comps()
    cid = "cmp_" + uuid.uuid4().hex[:12]
    items.append({
        "id": cid,
        "property_id": property_id,
        "sold_price": float(sold_price),
        "sold_date": sold_date,
        "address": address,
        "bed": bed,
        "bath": bath,
        "sqft": sqft,
        "distance_km": distance_km,
        "notes": notes,
        "created_at": _utcnow_iso(),
    })
    store.save_comps(items)
    return {"id": cid, "property_id": property_id}

def list_comps_for_property(property_id: str, limit: int = 200) -> List[Dict[str, Any]]:
    items = store.list_comps()
    return [x for x in items if x.get("property_id") == property_id][:limit]

def quick_arv(property_id: str) -> Dict[str, Any]:
    comps = list_comps_for_property(property_id)
    if not comps:
        return {"property_id": property_id, "arv": None, "method": "none", "count": 0}
    
    prices = sorted([c.get("sold_price") for c in comps if c.get("sold_price")])
    if not prices:
        return {"property_id": property_id, "arv": None, "method": "none", "count": len(comps)}
    
    mid = len(prices) // 2
    if len(prices) % 2 == 1:
        arv = prices[mid]
    else:
        arv = (prices[mid - 1] + prices[mid]) / 2
    
    return {"property_id": property_id, "arv": arv, "method": "median_sold_price", "count": len(comps)}
