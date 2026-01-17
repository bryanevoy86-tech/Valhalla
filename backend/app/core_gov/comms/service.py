from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def _dedupe(xs: List[str]) -> List[str]:
    out, seen = [], set()
    for x in xs or []:
        x2 = _norm(x)
        if x2 and x2 not in seen:
            seen.add(x2)
            out.append(x2)
    return out


def create_message(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = _norm(payload.get("title") or "")
    if not title:
        raise ValueError("title is required")

    now = _utcnow_iso()
    mid = "cm_" + uuid.uuid4().hex[:12]
    rec = {
        "id": mid,
        "title": title,
        "channel": payload.get("channel") or "email",
        "status": payload.get("status") or "draft",
        "tone": payload.get("tone") or "neutral",
        "to": _norm(payload.get("to") or ""),
        "subject": payload.get("subject") or "",
        "body": payload.get("body") or "",
        "deal_id": _norm(payload.get("deal_id") or ""),
        "contact_id": _norm(payload.get("contact_id") or ""),
        "partner_id": _norm(payload.get("partner_id") or ""),
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "sent_at": "",
        "created_at": now,
        "updated_at": now,
    }
    items = store.list_msgs()
    items.append(rec)
    store.save_msgs(items)
    return rec


def list_messages(status: Optional[str] = None, channel: Optional[str] = None, deal_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_msgs()
    if status:
        items = [x for x in items if x.get("status") == status]
    if channel:
        items = [x for x in items if x.get("channel") == channel]
    if deal_id:
        items = [x for x in items if x.get("deal_id") == deal_id]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items


def get_message(msg_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_msgs():
        if x["id"] == msg_id:
            return x
    return None


def patch_message(msg_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_msgs()
    tgt = None
    for x in items:
        if x["id"] == msg_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("message not found")

    for k in ["title","channel","status","tone","to","deal_id","contact_id","partner_id"]:
        if k in patch:
            tgt[k] = _norm(patch.get(k) or "") if k in ("title","to","deal_id","contact_id","partner_id") else patch.get(k)
    if "subject" in patch:
        tgt["subject"] = patch.get("subject") or ""
    if "body" in patch:
        tgt["body"] = patch.get("body") or ""
    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_msgs(items)
    return tgt


def mark_sent(msg_id: str, sent_at: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    items = store.list_msgs()
    tgt = None
    for x in items:
        if x["id"] == msg_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("message not found")

    tgt["status"] = "sent"
    tgt["sent_at"] = sent_at or _utcnow_iso()
    tgt["meta"] = {**(tgt.get("meta") or {}), **meta}
    tgt["updated_at"] = _utcnow_iso()
    store.save_msgs(items)
    return tgt
