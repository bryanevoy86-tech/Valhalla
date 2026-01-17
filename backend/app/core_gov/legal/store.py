from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "legal")
PROFILES_PATH = os.path.join(DATA_DIR, "profiles.json")
RULES_PATH = os.path.join(DATA_DIR, "rules.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PROFILES_PATH):
        with open(PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)
    if not os.path.exists(RULES_PATH):
        with open(RULES_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


def _read(path: str) -> Dict[str, Any]:
    _ensure()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(path: str, data: Dict[str, Any]) -> None:
    _ensure()
    data["updated_at"] = _utcnow_iso()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


# ---- Profiles ----
def list_profiles() -> List[Dict[str, Any]]:
    data = _read(PROFILES_PATH)
    return data.get("items", [])


def save_profiles(items: List[Dict[str, Any]]) -> None:
    _write(PROFILES_PATH, {"items": items})


# ---- Rules ----
def list_rules() -> List[Dict[str, Any]]:
    data = _read(RULES_PATH)
    return data.get("items", [])


def save_rules(items: List[Dict[str, Any]]) -> None:
    _write(RULES_PATH, {"items": items})
