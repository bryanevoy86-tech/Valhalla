from __future__ import annotations

from pathlib import Path
import datetime as dt
import uuid
from typing import Any

from app.core_gov.storage.json_store import read_json, write_json

CONTACTS_PATH = Path("data") / "deal_contacts.json"

def _now_utc() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"

def load_contacts() -> list[dict[str, Any]]:
    raw = read_json(CONTACTS_PATH)
    if not raw:
        return []
    items = raw.get("items", [])
    return items if isinstance(items, list) else []

def save_contacts(items: list[dict[str, Any]]) -> None:
    write_json(CONTACTS_PATH, {"items": items})

def add_contact(deal_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    items = load_contacts()
    contact = {
        "id": str(uuid.uuid4()),
        "deal_id": deal_id,
        "created_at_utc": _now_utc(),
        **payload,
    }
    items.append(contact)
    if len(items) > 50000:
        items = items[-50000:]
    save_contacts(items)
    return contact

def list_contacts_for_deal(deal_id: str, limit: int = 50) -> list[dict[str, Any]]:
    items = load_contacts()
    out = [c for c in items if c.get("deal_id") == deal_id]
    return out[-limit:][::-1]
