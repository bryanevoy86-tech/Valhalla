from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(name: str, amount: float, frequency: str = "monthly", next_date: str = "", currency: str = "CAD", notes: str = "") -> Dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    freq = (frequency or "monthly").strip().lower()  # one_time|weekly|biweekly|monthly|quarterly|yearly
    rec = {
        "id": store.new_id(),
        "name": name,
        "amount": float(amount or 0.0),
        "frequency": freq,
        "next_date": (next_date or "").strip(),  # YYYY-MM-DD optional
        "currency": (currency or "CAD").strip().upper(),
        "notes": notes or "",
        "status": "active",
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
    items.sort(key=lambda x: x.get("name","").lower())
    return items[:5000]
