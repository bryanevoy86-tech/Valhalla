from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(channel: str, to: str, subject: str = "", body: str = "", related: Dict[str, Any] | None = None) -> Dict[str, Any]:
    channel = (channel or "sms").strip().lower()
    to = (to or "").strip()
    if not to:
        raise ValueError("to required")
    rec = {
        "id": store.new_id(),
        "channel": channel,
        "to": to,
        "subject": subject or "",
        "body": body or "",
        "related": related or {},
        "status": "draft",
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
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items[:2000]

def mark_ready(outbox_id: str) -> Dict[str, Any]:
    items = store.list_items()
    tgt = next((x for x in items if x.get("id") == outbox_id), None)
    if not tgt:
        raise KeyError("not found")
    tgt["status"] = "ready"
    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt

def mark_sent(outbox_id: str, sent_via: str = "manual") -> Dict[str, Any]:
    items = store.list_items()
    tgt = next((x for x in items if x.get("id") == outbox_id), None)
    if not tgt:
        raise KeyError("not found")
    tgt["status"] = "sent"
    tgt["sent_via"] = sent_via
    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt
