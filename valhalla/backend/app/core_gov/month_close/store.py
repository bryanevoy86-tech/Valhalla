"""P-MONTHCLOSE-1: Month close storage."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

PATH = "backend/data/month_close/items.json"

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure_dir():
    os.makedirs(os.path.dirname(PATH), exist_ok=True)

def create(month: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Create a month close snapshot."""
    _ensure_dir()
    items: List[Dict[str, Any]] = []
    if os.path.exists(PATH):
        try:
            with open(PATH) as f:
                items = json.load(f).get("items", [])
        except:
            items = []
    
    item = {
        "id": f"mcs_{uuid.uuid4().hex[:12]}",
        "month": month,
        "snapshot": snapshot,
        "created_at": _utcnow_iso(),
    }
    items.append(item)
    
    tmp = PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return item

def list_items() -> List[Dict[str, Any]]:
    """List all month close snapshots."""
    _ensure_dir()
    if not os.path.exists(PATH):
        return []
    try:
        with open(PATH) as f:
            return json.load(f).get("items", [])
    except:
        return []

def get_by_month(month: str) -> Dict[str, Any] | None:
    """Get month close snapshot by month (YYYY-MM)."""
    items = list_items()
    for item in items:
        if item.get("month") == month:
            return item
    return None
