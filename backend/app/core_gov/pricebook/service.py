from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _norm(s: str) -> str:
    return (s or "").strip()

def create(item_name: str, typical_unit_price: float, unit: str = "each", preferred_store: str = "", status: str = "active", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    item_name = _norm(item_name)
    if not item_name:
        raise ValueError("item_name required")

    rec = {
        "id": "pb_" + uuid.uuid4().hex[:12],
        "item_name": item_name,
        "typical_unit_price": float(typical_unit_price or 0.0),
        "unit": _norm(unit or "each") or "each",
        "preferred_store": _norm(preferred_store),
        "status": status or "active",
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("item_name","").lower())
    return items

def find(item_name: str) -> Optional[Dict[str, Any]]:
    key = _norm(item_name).lower()
    for x in store.list_items():
        if (x.get("item_name") or "").strip().lower() == key and x.get("status","active") == "active":
            return x
    return None
