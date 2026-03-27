from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "inventory")
ITEMS_PATH = os.path.join(DATA_DIR, "items.json")
LOGS_PATH = os.path.join(DATA_DIR, "logs.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(ITEMS_PATH):
        with open(ITEMS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(LOGS_PATH):
        with open(LOGS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


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


def list_logs() -> List[Dict[str, Any]]:
    return _read(LOGS_PATH).get("items", [])


def save_logs(items: List[Dict[str, Any]]) -> None:
    _write(LOGS_PATH, items)
