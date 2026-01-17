from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, Body
from datetime import datetime, timezone
from . import store

router = APIRouter(prefix="/core/know/sources", tags=["core-know-sources"])

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

@router.post("")
def add(domain: str, expert: str = "", category: str = "", title: str = "", notes: str = "", tags: List[str] = Body(default=[])):
    rec = {
        "id": store.new_id(),
        "domain": (domain or "").strip(),        # legal/accounting/wholesaling/arbitrage/negotiation/etc.
        "expert": (expert or "").strip(),        # "top 10" name
        "category": (category or "").strip(),    # book/course/podcast/site
        "title": (title or "").strip(),
        "notes": notes or "",
        "tags": tags or [],
        "status": "queued",  # queued|in_progress|done
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    items = store.list_sources()
    items.append(rec)
    store.save_sources(items)
    return rec

@router.get("")
def list_items(domain: str = "", status: str = ""):
    items = store.list_sources()
    if domain:
        items = [x for x in items if x.get("domain") == domain]
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return {"items": items[:2000]}
