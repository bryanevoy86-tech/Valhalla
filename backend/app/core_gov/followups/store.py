from __future__ import annotations

from pathlib import Path
import datetime as dt
import uuid
from typing import Any

from app.core_gov.storage.json_store import read_json, write_json

FOLLOWUPS_PATH = Path("data") / "followups.json"

def _now_utc() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"

def load_followups() -> list[dict[str, Any]]:
    raw = read_json(FOLLOWUPS_PATH)
    if not raw:
        return []
    items = raw.get("items", [])
    return items if isinstance(items, list) else []

def save_followups(items: list[dict[str, Any]]) -> None:
    write_json(FOLLOWUPS_PATH, {"items": items})

def create_followup(payload: dict[str, Any]) -> dict[str, Any]:
    items = load_followups()
    fu = {
        "id": str(uuid.uuid4()),
        "created_at_utc": _now_utc(),
        "status": "open",  # open|done|canceled
        **payload,
    }
    items.append(fu)
    if len(items) > 50000:
        items = items[-50000:]
    save_followups(items)
    return fu

def update_followup(fu_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    items = load_followups()
    for i, f in enumerate(items):
        if f.get("id") == fu_id:
            f = {**f, **patch, "updated_at_utc": _now_utc()}
            items[i] = f
            save_followups(items)
            return f
    return None

def queue(limit: int = 50, due_before_utc: str | None = None, status: str = "open") -> list[dict[str, Any]]:
    items = load_followups()
    out = [f for f in items if (f.get("status") or "open") == status]
    if due_before_utc:
        out = [f for f in out if (f.get("due_at_utc") or "") <= due_before_utc]
    out.sort(key=lambda x: (x.get("due_at_utc") or "9999"))
    return out[:limit]
