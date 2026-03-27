from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "credit")
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
ACCOUNTS_PATH = os.path.join(DATA_DIR, "accounts.json")
TASKS_PATH = os.path.join(DATA_DIR, "tasks.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "profile": {}}, f, indent=2)
    if not os.path.exists(ACCOUNTS_PATH):
        with open(ACCOUNTS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(TASKS_PATH):
        with open(TASKS_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


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


def get_profile() -> Dict[str, Any]:
    return _read(PROFILE_PATH).get("profile", {})


def save_profile(profile: Dict[str, Any]) -> None:
    _write(PROFILE_PATH, {"updated_at": _utcnow_iso(), "profile": profile})


def list_accounts() -> List[Dict[str, Any]]:
    return _read(ACCOUNTS_PATH).get("items", [])


def save_accounts(items: List[Dict[str, Any]]) -> None:
    _write(ACCOUNTS_PATH, {"updated_at": _utcnow_iso(), "items": items})


def list_tasks() -> List[Dict[str, Any]]:
    return _read(TASKS_PATH).get("items", [])


def save_tasks(items: List[Dict[str, Any]]) -> None:
    _write(TASKS_PATH, {"updated_at": _utcnow_iso(), "items": items})
