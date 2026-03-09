from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "flow")
ITEMS_PATH = os.path.join(DATA_DIR, "items.json")
INVENTORY_PATH = os.path.join(DATA_DIR, "inventory.json")
SHOPPING_PATH = os.path.join(DATA_DIR, "shopping.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    for p, seed in [
        (ITEMS_PATH, {"updated_at": _utcnow_iso(), "items": []}),
        (INVENTORY_PATH, {"updated_at": _utcnow_iso(), "items": []}),
        (SHOPPING_PATH, {"updated_at": _utcnow_iso(), "items": []}),
    ]:
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                json.dump(seed, f, indent=2)


def _read(path: str) -> Dict[str, Any]:
    _ensure()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(path: str, items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def list_items() -> List[Dict[str, Any]]:
    return _read(ITEMS_PATH).get("items", [])


def save_items(items: List[Dict[str, Any]]) -> None:
    _write(ITEMS_PATH, items)


def list_inventory() -> List[Dict[str, Any]]:
    return _read(INVENTORY_PATH).get("items", [])


def save_inventory(items: List[Dict[str, Any]]) -> None:
    _write(INVENTORY_PATH, items)


def list_shopping() -> List[Dict[str, Any]]:
    return _read(SHOPPING_PATH).get("items", [])


def save_shopping(items: List[Dict[str, Any]]) -> None:
    _write(SHOPPING_PATH, items)
