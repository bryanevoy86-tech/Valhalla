from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def upsert(name: str, location: str = "pantry", qty: float = 0.0, min_qty: float = 0.0, unit: str = "each", priority: str = "normal", category: str = "grocery", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    location = (location or "pantry").strip().lower()

    items = store.list_items()
    existing = None
    for x in items:
        if (x.get("name","").lower() == name.lower()) and (x.get("location","").lower() == location):
            existing = x
            break

    if existing:
        existing.update({
            "qty": float(qty or 0.0),
            "min_qty": float(min_qty or 0.0),
            "unit": (unit or "each").strip(),
            "priority": (priority or "normal").strip(),
            "category": (category or "grocery").strip(),
            "notes": notes or existing.get("notes",""),
            "meta": {**(existing.get("meta") or {}), **meta},
            "updated_at": _utcnow_iso(),
        })
        store.save_items(items)
        return existing

    rec = {
        "id": "inv_" + uuid.uuid4().hex[:12],
        "name": name,
        "location": location,
        "qty": float(qty or 0.0),
        "min_qty": float(min_qty or 0.0),
        "unit": (unit or "each").strip(),
        "priority": (priority or "normal").strip(),
        "category": (category or "grocery").strip(),
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(location: str = "", category: str = "", low_only: bool = False, q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if location:
        ll = location.strip().lower()
        items = [x for x in items if (x.get("location","").lower() == ll)]
    if category:
        items = [x for x in items if (x.get("category","") == category)]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("name","").lower()) or qq in (x.get("notes","").lower())]
    if low_only:
        items = [x for x in items if float(x.get("qty") or 0.0) <= float(x.get("min_qty") or 0.0)]
    items.sort(key=lambda x: (x.get("location",""), x.get("category",""), x.get("name","")))
    return items[:5000]

def low_stock() -> List[Dict[str, Any]]:
    return list_items(low_only=True)
