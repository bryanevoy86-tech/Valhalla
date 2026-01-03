from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def add(item: str, qty: float = 1.0, unit: str = "each", priority: str = "normal", category: str = "grocery", notes: str = "", status: str = "open", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    item = (item or "").strip()
    if not item:
        raise ValueError("item required")
    rec = {
        "id": "shp_" + uuid.uuid4().hex[:12],
        "item": item,
        "qty": float(qty or 1.0),
        "unit": (unit or "each").strip(),
        "priority": (priority or "normal").strip(),
        "category": (category or "grocery").strip(),
        "notes": notes or "",
        "status": status,  # open/bought/removed
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "open", category: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if category:
        items = [x for x in items if x.get("category") == category]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("item","").lower()) or qq in (x.get("notes","").lower())]
    pr = {"high": 0, "normal": 1, "low": 2}
    items.sort(key=lambda x: (pr.get((x.get("priority") or "normal").lower(), 9), x.get("item","")))
    return items[:5000]

def mark(item_id: str, status: str) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == item_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("item not found")
    tgt["status"] = (status or "").strip()
    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt
