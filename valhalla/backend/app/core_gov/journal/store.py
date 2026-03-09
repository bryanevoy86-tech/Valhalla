"""P-JOURNAL-1: Journal storage."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

PATH = "backend/data/journal/items.json"

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure_dir():
    os.makedirs(os.path.dirname(PATH), exist_ok=True)

def add(text: str, tags: List[str] | None = None) -> Dict[str, Any]:
    """Add a journal entry (brain dump, note)."""
    _ensure_dir()
    items: List[Dict[str, Any]] = []
    if os.path.exists(PATH):
        try:
            with open(PATH) as f:
                items = json.load(f).get("items", [])
        except:
            items = []
    
    item = {
        "id": f"jrl_{uuid.uuid4().hex[:12]}",
        "text": text,
        "tags": tags or [],
        "created_at": _utcnow_iso(),
    }
    items.append(item)
    
    tmp = PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return item

def list_items(limit: int = 50) -> List[Dict[str, Any]]:
    """List recent journal entries."""
    _ensure_dir()
    if not os.path.exists(PATH):
        return []
    try:
        with open(PATH) as f:
            items = json.load(f).get("items", [])
        return items[-limit:] if limit else items
    except:
        return []

def search(query: str) -> List[Dict[str, Any]]:
    """Search journal entries by text."""
    items = list_items(limit=None)
    query_lower = query.lower()
    return [item for item in items if query_lower in item.get("text", "").lower()]
