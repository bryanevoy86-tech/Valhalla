from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "docs")
DOCS_PATH = os.path.join(DATA_DIR, "docs.json")
BUNDLES_PATH = os.path.join(DATA_DIR, "bundles.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DOCS_PATH):
        with open(DOCS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(BUNDLES_PATH):
        with open(BUNDLES_PATH, "w", encoding="utf-8") as f:
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


def list_docs() -> List[Dict[str, Any]]:
    return _read(DOCS_PATH).get("items", [])


def save_docs(items: List[Dict[str, Any]]) -> None:
    _write(DOCS_PATH, items)


def list_bundles() -> List[Dict[str, Any]]:
    return _read(BUNDLES_PATH).get("items", [])


def save_bundles(items: List[Dict[str, Any]]) -> None:
    _write(BUNDLES_PATH, items)
