from __future__ import annotations

import json, os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "mode")
PATH = os.path.join(DATA_DIR, "state.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "mode": "execute", "reason": ""}, f, indent=2)

def get_state() -> Dict[str, Any]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def set_state(mode: str, reason: str = "") -> Dict[str, Any]:
    _ensure()
    mode = (mode or "").strip().lower()
    if mode not in ("explore", "execute"):
        raise ValueError("mode must be explore|execute")
    state = {"updated_at": _utcnow_iso(), "mode": mode, "reason": reason or ""}
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return state
