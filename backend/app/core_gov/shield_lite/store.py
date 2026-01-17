from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "shield_lite")
PATH = os.path.join(DATA_DIR, "state.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({
                "updated_at": _utcnow(),
                "enabled": True,
                "active": False,
                "reason": "",
                "triggered_at": "",
                "notes": "",
            }, f, indent=2)

def get_state() -> Dict[str, Any]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def set_state(state: Dict[str, Any]) -> Dict[str, Any]:
    _ensure()
    state["updated_at"] = _utcnow()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return state
