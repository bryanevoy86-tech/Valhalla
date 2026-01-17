from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(name: str, kind: str = "chequing", currency: str = "CAD", masked: str = "", notes: str = "", status: str = "active") -> Dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    rec = {
        "id": "acc_" + uuid.uuid4().hex[:12],
        "name": name,
        "kind": (kind or "chequing").strip().lower(),
        "currency": (currency or "CAD").strip().upper(),
        "masked": masked or "",
        "notes": notes or "",
        "status": status,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "active") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("name",""))
    return items[:5000]
