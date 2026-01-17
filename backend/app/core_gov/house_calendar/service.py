from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(title: str, date: str, time: str = "", location: str = "", category: str = "household", notes: str = "", status: str = "active", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    title = (title or "").strip()
    if not title:
        raise ValueError("title required")
    if not (date or "").strip():
        raise ValueError("date required (YYYY-MM-DD)")

    rec = {
        "id": "evt_" + uuid.uuid4().hex[:12],
        "title": title,
        "date": date.strip(),
        "time": (time or "").strip(),  # optional "HH:MM"
        "location": location or "",
        "category": category or "household",
        "notes": notes or "",
        "status": status,
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(date_from: str = "", date_to: str = "", category: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if date_from:
        items = [x for x in items if x.get("date","") >= date_from]
    if date_to:
        items = [x for x in items if x.get("date","") <= date_to]
    if category:
        items = [x for x in items if x.get("category") == category]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("title","").lower()) or qq in (x.get("notes","").lower())]
    items.sort(key=lambda x: (x.get("date",""), x.get("time","")))
    return items[:5000]
