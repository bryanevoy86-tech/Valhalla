from __future__ import annotations

import json, os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "inventory")
LOC_PATH = os.path.join(DATA_DIR, "locations.json")
ITEMS_PATH = os.path.join(DATA_DIR, "items.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(LOC_PATH):
        with open(LOC_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(ITEMS_PATH):
        with open(ITEMS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)

def list_locations() -> List[Dict[str, Any]]:
    _ensure()
    with open(LOC_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

def save_locations(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = LOC_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, LOC_PATH)

def list_items() -> List[Dict[str, Any]]:
    _ensure()
    with open(ITEMS_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

def save_items(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = ITEMS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ITEMS_PATH)
