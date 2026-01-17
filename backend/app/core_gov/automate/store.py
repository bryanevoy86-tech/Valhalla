from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "automate")
RULES_PATH = os.path.join(DATA_DIR, "rules.json")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(RULES_PATH):
        with open(RULES_PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)


def _read() -> Dict[str, Any]:
    _ensure()
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = RULES_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, RULES_PATH)


def list_rules() -> List[Dict[str, Any]]:
    return _read().get("items", [])


def save_rules(items: List[Dict[str, Any]]) -> None:
    _write(items)
