from __future__ import annotations

from pathlib import Path
import datetime as dt
import uuid
from typing import Any

from app.core_gov.storage.json_store import read_json, write_json

BUYERS_PATH = Path("data") / "buyers.json"

def _now_utc() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"

def load_buyers() -> list[dict[str, Any]]:
    raw = read_json(BUYERS_PATH)
    if not raw:
        return []
    items = raw.get("items", [])
    return items if isinstance(items, list) else []

def save_buyers(items: list[dict[str, Any]]) -> None:
    write_json(BUYERS_PATH, {"items": items})

def add_buyer(payload: dict[str, Any]) -> dict[str, Any]:
    items = load_buyers()
    now = _now_utc()
    b = {**payload, "id": str(uuid.uuid4()), "created_at_utc": now, "updated_at_utc": now}
    items.append(b)
    if len(items) > 20000:
        items = items[-20000:]
    save_buyers(items)
    return b

def list_buyers(limit: int = 50, country: str | None = None) -> list[dict[str, Any]]:
    items = load_buyers()
    out = items
    if country:
        out = [b for b in out if (b.get("country") or "").upper() == country.upper()]
    return out[-limit:][::-1]
