from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "boring")
ENGINES_PATH = os.path.join(DATA_DIR, "engines.json")
RUNS_PATH = os.path.join(DATA_DIR, "runs.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(ENGINES_PATH):
        with open(ENGINES_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(RUNS_PATH):
        with open(RUNS_PATH, "w", encoding="utf-8") as f:
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


def list_engines() -> List[Dict[str, Any]]:
    return _read(ENGINES_PATH).get("items", [])


def save_engines(items: List[Dict[str, Any]]) -> None:
    _write(ENGINES_PATH, items)


def list_runs() -> List[Dict[str, Any]]:
    return _read(RUNS_PATH).get("items", [])


def save_runs(items: List[Dict[str, Any]]) -> None:
    _write(RUNS_PATH, items)
