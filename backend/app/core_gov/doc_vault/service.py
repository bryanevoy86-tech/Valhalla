from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(title: str, kind: str = "note", file_path: str = "", tags: List[str] | None = None, links: Dict[str, str] | None = None, notes: str = "") -> Dict[str, Any]:
    title = (title or "").strip()
    if not title:
        raise ValueError("title required")

    rec = {
        "id": store.new_id(),
        "title": title,
        "kind": (kind or "note").strip().lower(),  # note|pdf|image|contract|receipt|other
        "file_path": (file_path or "").strip(),
        "tags": tags or [],
        "links": links or {},  # {"deal_id": "...", "partner_id": "..."} etc.
        "notes": notes or "",
        "status": "active",
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    docs = store.list_docs()
    docs.append(rec)
    store.save_docs(docs)
    return rec

def list_docs(tag: str = "", kind: str = "", status: str = "active", limit: int = 100) -> List[Dict[str, Any]]:
    docs = store.list_docs()
    if status:
        docs = [d for d in docs if d.get("status") == status]
    if kind:
        docs = [d for d in docs if d.get("kind") == kind]
    if tag:
        t = tag.strip().lower()
        docs = [d for d in docs if t in [x.lower() for x in (d.get("tags") or [])]]
    docs.sort(key=lambda d: d.get("updated_at",""), reverse=True)
    return docs[:max(1, min(2000, int(limit or 100)))]

def get(doc_id: str) -> Dict[str, Any] | None:
    return next((d for d in store.list_docs() if d.get("id") == doc_id), None)

def patch(doc_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    docs = store.list_docs()
    d = next((x for x in docs if x.get("id") == doc_id), None)
    if not d:
        raise KeyError("not found")
    patch = patch or {}
    for k in ("title","kind","file_path","notes","status"):
        if k in patch:
            d[k] = patch[k]
    if "tags" in patch and isinstance(patch["tags"], list):
        d["tags"] = patch["tags"]
    if "links" in patch and isinstance(patch["links"], dict):
        d["links"] = patch["links"]
    d["updated_at"] = _utcnow_iso()
    store.save_docs(docs)
    return d
