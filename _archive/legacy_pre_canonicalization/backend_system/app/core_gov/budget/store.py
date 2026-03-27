from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "budget")
BUCKETS_PATH = os.path.join(DATA_DIR, "buckets.json")
SNAPSHOTS_PATH = os.path.join(DATA_DIR, "snapshots.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(BUCKETS_PATH):
        with open(BUCKETS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(SNAPSHOTS_PATH):
        with open(SNAPSHOTS_PATH, "w", encoding="utf-8") as f:
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


def list_buckets() -> List[Dict[str, Any]]:
    return _read(BUCKETS_PATH).get("items", [])


def save_buckets(items: List[Dict[str, Any]]) -> None:
    _write(BUCKETS_PATH, items)


def list_snapshots() -> List[Dict[str, Any]]:
    return _read(SNAPSHOTS_PATH).get("items", [])


def save_snapshots(items: List[Dict[str, Any]]) -> None:
    _write(SNAPSHOTS_PATH, items)
