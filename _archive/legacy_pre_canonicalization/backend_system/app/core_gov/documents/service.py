from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _norm(s: str) -> str:
    return (s or "").strip()

def create(title: str, doc_type: str = "general", tags: List[str] = None, local_path: str = "", source: str = "manual", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    tags = tags or []
    meta = meta or {}

    title = _norm(title)
    if not title:
        raise ValueError("title required")

    rec = {
        "id": "doc_" + uuid.uuid4().hex[:12],
        "title": title,
        "doc_type": _norm(doc_type or "general") or "general",
        "tags": tags,
        "local_path": _norm(local_path),
        "source": _norm(source or "manual") or "manual",
        "status": "active",  # active/archived
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "", doc_type: str = "", tag: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if doc_type:
        items = [x for x in items if (x.get("doc_type") or "") == doc_type]
    if tag:
        tt = tag.strip().lower()
        items = [x for x in items if any((t or "").lower() == tt for t in (x.get("tags") or []))]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("title","").lower()) or qq in (x.get("notes","").lower())]
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[:500]

def get_one(doc_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_items():
        if x.get("id") == doc_id:
            return x
    return None

def patch(doc_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == doc_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("doc not found")

    for k in ["title","doc_type","local_path","source","status","notes"]:
        if k in patch:
            v = patch.get(k)
            if k in ("title","doc_type","local_path","source","status"):
                v = _norm(v or "")
            tgt[k] = v
    if "tags" in patch:
        tgt["tags"] = patch.get("tags") or []
    if "meta" in patch:
        tgt["meta"] = patch.get("meta") or {}

    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt
