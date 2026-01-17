from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _norm(s: str) -> str:
    return (s or "").strip()

def create(name: str, channel: str, subject: str = "", body: str = "", tags: List[str] = None, status: str = "active", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    tags = tags or []
    meta = meta or {}
    channel = _norm(channel).lower()
    if channel not in ("sms","email","call","letter","dm"):
        raise ValueError("channel must be sms|email|call|letter|dm")
    name = _norm(name)
    if not name:
        raise ValueError("name required")

    rec = {
        "id": "tpl_" + uuid.uuid4().hex[:12],
        "name": name,
        "channel": channel,
        "subject": subject or "",
        "body": body or "",
        "tags": tags,
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

def list_items(status: str = "", channel: str = "", tag: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if channel:
        items = [x for x in items if x.get("channel") == channel]
    if tag:
        tt = tag.strip().lower()
        items = [x for x in items if any((t or "").lower() == tt for t in (x.get("tags") or []))]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("name","").lower()) or qq in (x.get("body","").lower())]
    items.sort(key=lambda x: x.get("name",""))
    return items[:1000]

def get_one(tpl_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_items():
        if x.get("id") == tpl_id:
            return x
    return None

def render(tpl: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    Very safe string replacement: {{var}}
    """
    variables = variables or {}
    subj = tpl.get("subject","") or ""
    body = tpl.get("body","") or ""
    for k, v in variables.items():
        token = "{{" + str(k) + "}}"
        subj = subj.replace(token, str(v))
        body = body.replace(token, str(v))
    return {"channel": tpl.get("channel",""), "subject": subj, "body": body}
