from __future__ import annotations

import uuid
from datetime import datetime, timezone, date
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def _dedupe(tags: List[str]) -> List[str]:
    out, seen = [], set()
    for t in tags or []:
        t2 = _norm(t)
        if t2 and t2 not in seen:
            seen.add(t2)
            out.append(t2)
    return out


def _validate_date(s: str) -> None:
    try:
        date.fromisoformat(s)
    except Exception:
        raise ValueError("due_date must be YYYY-MM-DD")


def create(payload: Dict[str, Any]) -> Dict[str, Any]:
    title = _norm(payload.get("title") or "")
    if not title:
        raise ValueError("title is required")
    due_date = _norm(payload.get("due_date") or "")
    _validate_date(due_date)

    now = _utcnow_iso()
    sid = "sc_" + uuid.uuid4().hex[:12]
    rec = {
        "id": sid,
        "title": title,
        "kind": payload.get("kind") or "task",
        "due_date": due_date,
        "due_time": _norm(payload.get("due_time") or ""),
        "timezone": payload.get("timezone") or "America/Toronto",
        "priority": payload.get("priority") or "B",
        "status": payload.get("status") or "open",
        "link_type": _norm(payload.get("link_type") or ""),
        "link_id": _norm(payload.get("link_id") or ""),
        "est_cost": float(payload.get("est_cost") or 0.0),
        "currency": _norm(payload.get("currency") or "CAD") or "CAD",
        "notes": payload.get("notes") or "",
        "tags": _dedupe(payload.get("tags") or []),
        "meta": payload.get("meta") or {},
        "created_at": now,
        "updated_at": now,
    }

    items = store.list_all()
    items.append(rec)
    store.save_all(items)
    return rec


def list_all(status: Optional[str] = None, priority: Optional[str] = None, due_date: Optional[str] = None) -> List[Dict[str, Any]]:
    items = store.list_all()
    if status:
        items = [x for x in items if x.get("status") == status]
    if priority:
        items = [x for x in items if x.get("priority") == priority]
    if due_date:
        items = [x for x in items if x.get("due_date") == due_date]
    return items


def patch(sid: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_all()
    tgt = None
    for x in items:
        if x["id"] == sid:
            tgt = x
            break
    if not tgt:
        raise KeyError("schedule item not found")

    for k in ["title","kind","due_time","timezone","priority","status","link_type","link_id","currency"]:
        if k in patch:
            if k in ("title","due_time","link_type","link_id","currency"):
                tgt[k] = _norm(patch.get(k) or "")
            else:
                tgt[k] = patch.get(k)

    if "due_date" in patch:
        d = _norm(patch.get("due_date") or "")
        _validate_date(d)
        tgt["due_date"] = d

    if "est_cost" in patch:
        tgt["est_cost"] = float(patch.get("est_cost") or 0.0)
    if "notes" in patch:
        tgt["notes"] = patch.get("notes") or ""
    if "tags" in patch:
        tgt["tags"] = _dedupe(patch.get("tags") or [])
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_all(items)
    return tgt
