from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "knowledge_ingest")
INBOX_PATH = os.path.join(DATA_DIR, "inbox.json")
CHUNKS_PATH = os.path.join(DATA_DIR, "chunks.json")
INDEX_PATH = os.path.join(DATA_DIR, "index.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    for p in [INBOX_PATH, CHUNKS_PATH, INDEX_PATH]:
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
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


def list_inbox() -> List[Dict[str, Any]]:
    return _read(INBOX_PATH).get("items", [])


def save_inbox(items: List[Dict[str, Any]]) -> None:
    _write(INBOX_PATH, items)


def list_chunks() -> List[Dict[str, Any]]:
    return _read(CHUNKS_PATH).get("items", [])


def save_chunks(items: List[Dict[str, Any]]) -> None:
    _write(CHUNKS_PATH, items)


def list_index() -> List[Dict[str, Any]]:
    return _read(INDEX_PATH).get("items", [])


def save_index(items: List[Dict[str, Any]]) -> None:
    _write(INDEX_PATH, items)
