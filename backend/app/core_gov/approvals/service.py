from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(
    title: str,
    action: str,
    target_type: str = "",
    target_id: str = "",
    cone_band: str = "",
    risk: str = "medium",
    payload: Dict[str, Any] = None,
    notes: str = "",
) -> Dict[str, Any]:
    payload = payload or {}
    title = (title or "").strip()
    action = (action or "").strip()
    if not title:
        raise ValueError("title required")
    if not action:
        raise ValueError("action required")

    rec = {
        "id": "apr_" + uuid.uuid4().hex[:12],
        "title": title,
        "action": action,
        "target_type": target_type or "",
        "target_id": target_id or "",
        "cone_band": (cone_band or "").strip().upper(),
        "risk": (risk or "medium").strip().lower(),  # low|medium|high
        "payload": payload,
        "notes": notes or "",
        "status": "pending",  # pending|approved|denied
        "decision": {"by": "", "at": "", "reason": ""},
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "pending") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    items.sort(key=lambda x: x.get("created_at",""), reverse=True)
    return items[:2000]

def get_one(approval_id: str) -> Optional[Dict[str, Any]]:
    return next((x for x in store.list_items() if x.get("id") == approval_id), None)

def decide(approval_id: str, decision: str, by: str = "owner", reason: str = "") -> Dict[str, Any]:
    decision = (decision or "").strip().lower()
    if decision not in ("approved","denied"):
        raise ValueError("decision must be approved|denied")

    items = store.list_items()
    tgt = next((x for x in items if x.get("id") == approval_id), None)
    if not tgt:
        raise KeyError("approval not found")

    tgt["status"] = decision
    tgt["decision"] = {"by": by or "owner", "at": _utcnow_iso(), "reason": reason or ""}
    tgt["updated_at"] = _utcnow_iso()
    store.save_items(items)
    return tgt
