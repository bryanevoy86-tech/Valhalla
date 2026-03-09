from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(match_field: str, contains: str, category: str, priority: int = 100, status: str = "active", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    mf = (match_field or "").strip().lower()
    if mf not in ("merchant","description"):
        raise ValueError("match_field must be merchant|description")
    c = (contains or "").strip()
    if not c:
        raise ValueError("contains required")
    if not (category or "").strip():
        raise ValueError("category required")

    rec = {
        "id": "cr_" + uuid.uuid4().hex[:12],
        "match_field": mf,
        "contains": c,
        "category": category.strip(),
        "priority": int(priority or 100),
        "status": status,
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "active", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("contains","").lower()) or qq in (x.get("category","").lower())]
    items.sort(key=lambda x: (int(x.get("priority") or 999999), x.get("category","")))
    return items[:5000]

def apply_one(merchant: str, description: str) -> str:
    m = (merchant or "").lower()
    d = (description or "").lower()
    for r in list_items(status="active"):
        field = r.get("match_field")
        needle = (r.get("contains") or "").lower()
        if field == "merchant" and needle in m:
            return r.get("category","")
        if field == "description" and needle in d:
            return r.get("category","")
    return ""
