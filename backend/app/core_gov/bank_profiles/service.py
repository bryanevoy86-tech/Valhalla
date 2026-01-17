from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create(name: str, mapping: Dict[str, Any], notes: str = "") -> Dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError("mapping must be a dict")

    rec = {
        "id": "bp_" + uuid.uuid4().hex[:12],
        "name": name,
        "mapping": mapping,
        "notes": notes or "",
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec


def list_items() -> List[Dict[str, Any]]:
    items = store.list_items()
    items.sort(key=lambda x: x.get("name",""))
    return items


def get_one(profile_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_items():
        if x.get("id") == profile_id:
            return x
    return None
