from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _norm(s: str) -> str:
    return (s or "").strip()

def link(doc_id: str, entity_type: str, entity_id: str, relation: str = "attachment", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    doc_id = _norm(doc_id)
    entity_type = _norm(entity_type)
    entity_id = _norm(entity_id)
    relation = _norm(relation or "attachment") or "attachment"
    if not doc_id:
        raise ValueError("doc_id required")
    if not entity_type:
        raise ValueError("entity_type required")
    if not entity_id:
        raise ValueError("entity_id required")

    rec = {
        "id": "dl_" + uuid.uuid4().hex[:12],
        "doc_id": doc_id,
        "entity_type": entity_type,   # deals, loans, grants, receipts, legal, partner...
        "entity_id": entity_id,
        "relation": relation,
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_links(entity_type: str = "", entity_id: str = "", doc_id: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if entity_type:
        items = [x for x in items if x.get("entity_type") == entity_type]
    if entity_id:
        items = [x for x in items if x.get("entity_id") == entity_id]
    if doc_id:
        items = [x for x in items if x.get("doc_id") == doc_id]
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[:1000]
