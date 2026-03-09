from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "obligations")
OBLIGATIONS_PATH = os.path.join(DATA_DIR, "obligations.json")
RUNS_PATH = os.path.join(DATA_DIR, "runs.json")
RESERVES_PATH = os.path.join(DATA_DIR, "reserves.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(OBLIGATIONS_PATH):
        with open(OBLIGATIONS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(RUNS_PATH):
        with open(RUNS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(RESERVES_PATH):
        with open(RESERVES_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "state": {}}, f, indent=2)


def _read(path: str) -> Dict[str, Any]:
    _ensure()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(path: str, payload: Dict[str, Any]) -> None:
    _ensure()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def list_obligations() -> List[Dict[str, Any]]:
    return _read(OBLIGATIONS_PATH).get("items", [])


def save_obligations(items: List[Dict[str, Any]]) -> None:
    _write(OBLIGATIONS_PATH, {"updated_at": _utcnow_iso(), "items": items})


def read_runs() -> List[Dict[str, Any]]:
    return _read(RUNS_PATH).get("items", [])


def save_runs(items: List[Dict[str, Any]]) -> None:
    _write(RUNS_PATH, {"updated_at": _utcnow_iso(), "items": items})


def read_reserves() -> Dict[str, Any]:
    return _read(RESERVES_PATH).get("state", {})


def save_reserves(state: Dict[str, Any]) -> None:
    _write(RESERVES_PATH, {"updated_at": _utcnow_iso(), "state": state})
