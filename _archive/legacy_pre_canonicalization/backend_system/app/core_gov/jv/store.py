from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "jv")
PARTNERS_PATH = os.path.join(DATA_DIR, "partners.json")
LINKS_PATH = os.path.join(DATA_DIR, "links.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PARTNERS_PATH):
        with open(PARTNERS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(LINKS_PATH):
        with open(LINKS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


def _read(path: str) -> Dict[str, Any]:
    _ensure()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(path: str, items: List[Dict[str, Any]]) -> None:
    _ensure()
    data = {"updated_at": _utcnow_iso(), "items": items}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def list_partners() -> List[Dict[str, Any]]:
    return _read(PARTNERS_PATH).get("items", [])


def save_partners(items: List[Dict[str, Any]]) -> None:
    _write(PARTNERS_PATH, items)


def list_links() -> List[Dict[str, Any]]:
    return _read(LINKS_PATH).get("items", [])


def save_links(items: List[Dict[str, Any]]) -> None:
    _write(LINKS_PATH, items)
