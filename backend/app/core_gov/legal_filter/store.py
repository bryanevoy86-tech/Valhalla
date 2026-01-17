from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "legal_filter")
PROFILES_PATH = os.path.join(DATA_DIR, "profiles.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PROFILES_PATH):
        with open(PROFILES_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


def list_profiles() -> List[Dict[str, Any]]:
    _ensure()
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])


def save_profiles(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = PROFILES_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PROFILES_PATH)
