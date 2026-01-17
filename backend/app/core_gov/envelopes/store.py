from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "envelopes")
PATH = os.path.join(DATA_DIR, "config.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

DEFAULT = {
    "updated_at": "",
    "envelopes": {
        "bills": 0.0,
        "groceries": 0.0,
        "fuel": 0.0,
        "kids": 0.0,
        "fun": 0.0,
        "savings": 0.0,
    }
}

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        d = dict(DEFAULT)
        d["updated_at"] = _utcnow_iso()
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)

def get() -> Dict[str, Any]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save(patch: Dict[str, Any]) -> Dict[str, Any]:
    d = get()
    if "envelopes" in (patch or {}) and isinstance(patch["envelopes"], dict):
        d["envelopes"] = {str(k).strip().lower(): float(v or 0.0) for k, v in patch["envelopes"].items()}
    d["updated_at"] = _utcnow_iso()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return d
