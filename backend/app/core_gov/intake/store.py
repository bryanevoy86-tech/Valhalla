from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import uuid
import datetime as dt

from ..storage.json_store import read_json, write_json

LEADS_PATH = Path("data") / "leads.json"

def _now_utc() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"

def load_leads() -> list[dict[str, Any]]:
    raw = read_json(LEADS_PATH)
    if not raw:
        return []
    items = raw.get("items", [])
    return items if isinstance(items, list) else []

def save_leads(items: list[dict[str, Any]]) -> None:
    write_json(LEADS_PATH, {"items": items})

def add_lead(payload: dict[str, Any]) -> dict[str, Any]:
    items = load_leads()
    lead = {
        **payload,
        "id": str(uuid.uuid4()),
        "created_at_utc": _now_utc(),
    }
    items.append(lead)
    # cap file size
    if len(items) > 5000:
        items = items[-5000:]
    save_leads(items)
    return lead

def list_leads(limit: int = 50) -> list[dict[str, Any]]:
    items = load_leads()
    return items[-limit:][::-1]  # newest first
