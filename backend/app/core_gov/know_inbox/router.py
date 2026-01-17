from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Body, HTTPException
from . import store
from datetime import datetime, timezone

router = APIRouter(prefix="/core/know/inbox", tags=["core-know-inbox"])

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.post("")
def add(title: str, file_path: str = "", tags: List[str] = Body(default=[]), notes: str = ""):
    title = (title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    rec = {
        "id": store.new_id(),
        "title": title,
        "file_path": (file_path or "").strip(),
        "tags": tags or [],
        "notes": notes or "",
        "status": "new",
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

@router.get("")
def list_items(status: str = ""):
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return {"items": items[:2000]}
