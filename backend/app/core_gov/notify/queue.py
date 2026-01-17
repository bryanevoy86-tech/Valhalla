from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Dict, List

_NOTIFICATIONS: List[Dict[str, Any]] = []

def push(level: str, title: str, detail: str, meta: dict | None = None) -> dict:
    n = {
        "id": str(uuid.uuid4()),
        "ts_utc": dt.datetime.utcnow().isoformat() + "Z",
        "level": level,  # info|yellow|red
        "title": title,
        "detail": detail,
        "meta": meta or {},
    }
    _NOTIFICATIONS.append(n)
    # cap list
    if len(_NOTIFICATIONS) > 200:
        _NOTIFICATIONS[:] = _NOTIFICATIONS[-200:]
    return n

def list_all(limit: int = 50) -> list[dict]:
    return _NOTIFICATIONS[-limit:]

def clear_all() -> dict:
    _NOTIFICATIONS.clear()
    return {"ok": True}
