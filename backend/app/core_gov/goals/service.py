from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(title: str, target_amount: float, due_date: str = "", vault_id: str = "", priority: str = "normal", notes: str = "") -> Dict[str, Any]:
    title = (title or "").strip()
    if not title:
        raise ValueError("title required")
    ta = float(target_amount or 0.0)
    if ta < 0:
        raise ValueError("target_amount must be >= 0")
    priority = (priority or "normal").strip().lower()
    if priority not in ("low","normal","high"):
        raise ValueError("priority must be low|normal|high")

    rec = {
        "id": "gol_" + uuid.uuid4().hex[:12],
        "title": title,
        "target_amount": ta,
        "due_date": due_date or "",
        "vault_id": vault_id or "",
        "priority": priority,
        "notes": notes or "",
        "status": "active",
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
    items.sort(key=lambda x: ({"high":0,"normal":1,"low":2}.get(x.get("priority","normal"),1), x.get("title","")))
    return items[:5000]
