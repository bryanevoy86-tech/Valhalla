from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _norm(s: str) -> str:
    return (s or "").strip()

def create_entity(entity_type: str, name: str, country: str = "CA", region_code: str = "", status: str = "active", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    entity_type = _norm(entity_type)
    name = _norm(name)
    if not entity_type:
        raise ValueError("entity_type required (corp|llc|trust|bank|insurance|vendor)")
    if not name:
        raise ValueError("name required")

    rec = {
        "id": "ent_" + uuid.uuid4().hex[:12],
        "entity_type": entity_type,
        "name": name,
        "country": _norm(country or "CA").upper(),
        "region_code": _norm(region_code).upper(),
        "status": status or "active",
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_entities()
    items.append(rec)
    store.save_entities(items)
    return rec

def list_entities(status: str = "", entity_type: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_entities()
    if status:
        items = [x for x in items if x.get("status") == status]
    if entity_type:
        items = [x for x in items if x.get("entity_type") == entity_type]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("name","").lower()) or qq in (x.get("notes","").lower())]
    items.sort(key=lambda x: (x.get("entity_type",""), x.get("name","")))
    return items[:1000]

def get_entity(entity_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_entities():
        if x.get("id") == entity_id:
            return x
    return None

def add_task(entity_id: str, title: str, status: str = "open", due_date: str = "", priority: str = "normal", requires_doc: bool = False, notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    entity_id = _norm(entity_id)
    title = _norm(title)
    if not entity_id:
        raise ValueError("entity_id required")
    if not title:
        raise ValueError("title required")
    if not get_entity(entity_id):
        raise ValueError("entity_id not found")

    rec = {
        "id": "et_" + uuid.uuid4().hex[:12],
        "entity_id": entity_id,
        "title": title,
        "status": status or "open",     # open/doing/done/blocked
        "due_date": _norm(due_date),
        "priority": _norm(priority or "normal") or "normal",
        "requires_doc": bool(requires_doc),
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_tasks()
    items.append(rec)
    store.save_tasks(items)
    return rec

def list_tasks(entity_id: str = "", status: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_tasks()
    if entity_id:
        items = [x for x in items if x.get("entity_id") == entity_id]
    if status:
        items = [x for x in items if x.get("status") == status]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("title","").lower()) or qq in (x.get("notes","").lower())]
    items.sort(key=lambda x: (x.get("status",""), x.get("due_date",""), x.get("created_at","")), reverse=True)
    return items[:1500]

def set_task_status(task_id: str, status: str) -> Dict[str, Any]:
    items = store.list_tasks()
    tgt = None
    for x in items:
        if x.get("id") == task_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("task not found")
    tgt["status"] = _norm(status)
    tgt["updated_at"] = _utcnow_iso()
    store.save_tasks(items)
    return tgt
