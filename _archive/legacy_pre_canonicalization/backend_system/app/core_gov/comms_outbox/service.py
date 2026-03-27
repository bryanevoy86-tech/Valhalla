from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _norm(s: str) -> str:
    return (s or "").strip()

def create(channel: str, to: str, subject: str = "", body: str = "", entity_type: str = "", entity_id: str = "", status: str = "draft", tags: List[str] = None, notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    tags = tags or []
    meta = meta or {}
    channel = _norm(channel).lower()
    if channel not in ("sms","email","call","letter","dm"):
        raise ValueError("channel must be sms|email|call|letter|dm")
    if not _norm(to):
        raise ValueError("to required")

    rec = {
        "id": "msg_" + uuid.uuid4().hex[:12],
        "channel": channel,
        "to": _norm(to),
        "subject": subject or "",
        "body": body or "",
        "entity_type": _norm(entity_type),
        "entity_id": _norm(entity_id),
        "status": status or "draft",  # draft/sent/archived
        "tags": tags,
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
        "sent_at": "",
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "", channel: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if channel:
        items = [x for x in items if x.get("channel") == channel]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("to","").lower()) or qq in (x.get("subject","").lower()) or qq in (x.get("body","").lower())]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items[:1000]

def mark_sent(msg_id: str) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == msg_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("message not found")
    tgt["status"] = "sent"
    tgt["sent_at"] = _utcnow_iso()
    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt
