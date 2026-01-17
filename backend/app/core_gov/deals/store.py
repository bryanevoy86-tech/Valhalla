from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import datetime as dt
import uuid

from app.core_gov.storage.json_store import read_json, write_json

DEALS_PATH = Path("data") / "deals.json"

def _now_utc() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"

def load_deals() -> list[dict[str, Any]]:
    raw = read_json(DEALS_PATH)
    if not raw:
        return []
    items = raw.get("items", [])
    return items if isinstance(items, list) else []

def save_deals(items: list[dict[str, Any]]) -> None:
    write_json(DEALS_PATH, {"items": items})

def add_deal(payload: dict[str, Any]) -> dict[str, Any]:
    items = load_deals()
    now = _now_utc()
    deal = {
        **payload,
        "id": str(uuid.uuid4()),
        "created_at_utc": now,
        "updated_at_utc": now,
    }
    items.append(deal)
    if len(items) > 20000:
        items = items[-20000:]
    save_deals(items)
    return deal

def update_deal(deal_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    items = load_deals()
    for i, d in enumerate(items):
        if d.get("id") == deal_id:
            d = {**d, **patch, "updated_at_utc": _now_utc()}
            items[i] = d
            save_deals(items)
            return d
    return None

def get_deal(deal_id: str) -> dict[str, Any] | None:
    items = load_deals()
    for d in items:
        if d.get("id") == deal_id:
            return d
    return None

def list_deals(limit: int = 50, stage: str | None = None, source: str | None = None) -> list[dict[str, Any]]:
    items = load_deals()
    out = items
    if stage:
        out = [d for d in out if d.get("stage") == stage]
    if source:
        out = [d for d in out if d.get("lead_source") == source]
    return out[-limit:][::-1]  # newest first
