from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "partners")
PARTNERS_PATH = os.path.join(DATA_DIR, "partners.json")
NOTES_PATH = os.path.join(DATA_DIR, "notes.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PARTNERS_PATH):
        with open(PARTNERS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(NOTES_PATH):
        with open(NOTES_PATH, "w", encoding="utf-8") as f:
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


def list_partners() -> List[Dict[str, Any]]:
    return _read(PARTNERS_PATH).get("items", [])


def save_partners(items: List[Dict[str, Any]]) -> None:
    _write(PARTNERS_PATH, items)


def list_notes() -> List[Dict[str, Any]]:
    return _read(NOTES_PATH).get("items", [])


def save_notes(items: List[Dict[str, Any]]) -> None:
    _write(NOTES_PATH, items)
