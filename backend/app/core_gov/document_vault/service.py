from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(
    title: str,
    doc_type: str = "note",
    tags: List[str] = None,
    source: str = "",
    file_path: str = "",
    text: str = "",
    links: List[Dict[str, Any]] = None,   # {type,id}
) -> Dict[str, Any]:
    title = (title or "").strip()
    if not title:
        raise ValueError("title required")

    rec = {
        "id": "doc_" + uuid.uuid4().hex[:12],
        "title": title,
        "doc_type": (doc_type or "note").strip(),
        "tags": tags or [],
        "source": source or "",
        "file_path": file_path or "",
        "text": text or "",
        "links": links or [],
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(tag: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if tag:
        items = [x for x in items if tag in (x.get("tags") or [])]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("title","").lower()) or qq in (x.get("text","").lower())]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items[:5000]

def get_one(doc_id: str) -> Optional[Dict[str, Any]]:
    return next((x for x in store.list_items() if x.get("id") == doc_id), None)

def add_tag(doc_id: str, tag: str) -> Dict[str, Any]:
    tag = (tag or "").strip()
    if not tag:
        raise ValueError("tag required")
    items = store.list_items()
    tgt = next((x for x in items if x.get("id") == doc_id), None)
    if not tgt:
        raise KeyError("not found")
    tgt.setdefault("tags", [])
    if tag not in tgt["tags"]:
        tgt["tags"].append(tag)
    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt

def link(doc_id: str, target_type: str, target_id: str) -> Dict[str, Any]:
    if not target_type or not target_id:
        raise ValueError("target_type and target_id required")
    items = store.list_items()
    tgt = next((x for x in items if x.get("id") == doc_id), None)
    if not tgt:
        raise KeyError("not found")
    tgt.setdefault("links", [])
    tgt["links"].append({"type": target_type, "id": target_id})
    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt
