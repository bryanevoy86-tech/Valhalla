from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import store


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(s: str) -> str:
    return (s or "").strip()


def log(payload: Dict[str, Any]) -> Dict[str, Any]:
    msg = _norm(payload.get("message") or "")
    if not msg:
        raise ValueError("message is required")

    rec = {
        "id": "ae_" + uuid.uuid4().hex[:12],
        "event_type": payload.get("event_type") or "custom",
        "level": payload.get("level") or "info",
        "message": msg,
        "actor": _norm(payload.get("actor") or "api"),
        "ref_type": _norm(payload.get("ref_type") or ""),
        "ref_id": _norm(payload.get("ref_id") or ""),
        "meta": payload.get("meta") or {},
        "created_at": _utcnow_iso(),
    }
    store.append_event(rec)
    return rec


def list_events(
    limit: int = 100,
    level: Optional[str] = None,
    event_type: Optional[str] = None,
    ref_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    items = list(reversed(store.read_events()))
    if level:
        items = [x for x in items if x.get("level") == level]
    if event_type:
        items = [x for x in items if x.get("event_type") == event_type]
    if ref_id:
        items = [x for x in items if x.get("ref_id") == ref_id]
    return items[: max(1, min(limit, 500))]
