from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(obligation_id: str, guide_id: str = "", status: str = "pending", notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    if not (obligation_id or "").strip():
        raise ValueError("obligation_id required")

    rec = {
        "id": "aps_" + uuid.uuid4().hex[:12],
        "obligation_id": obligation_id.strip(),
        "guide_id": (guide_id or "").strip(),
        "status": (status or "pending").strip(),
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
        "verified_at": "",
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "", obligation_id: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if obligation_id:
        items = [x for x in items if x.get("obligation_id") == obligation_id]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items[:2000]

def set_status(setup_id: str, status: str) -> Dict[str, Any]:
    items = store.list_items()
    tgt = None
    for x in items:
        if x.get("id") == setup_id:
            tgt = x
            break
    if not tgt:
        raise KeyError("setup not found")
    tgt["status"] = (status or "").strip()
    tgt["updated_at"] = _utcnow_iso()
    if tgt["status"] == "verified":
        tgt["verified_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt
