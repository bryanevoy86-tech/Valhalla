from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "command")
PATH = os.path.join(DATA_DIR, "mode.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "mode": "execute"}, f, indent=2)

def get() -> Dict[str, Any]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def set_mode(mode: str) -> Dict[str, Any]:
    _ensure()
    m = (mode or "").strip().lower()
    if m not in ("explore","execute"):
        raise ValueError("mode must be explore or execute")
    d = {"updated_at": _utcnow_iso(), "mode": m}
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2)
    os.replace(tmp, PATH)
    return d
