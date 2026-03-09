from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "house_budget")
PATH = os.path.join(DATA_DIR, "profile.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

DEFAULT = {
    "updated_at": "",
    "currency": "CAD",
    "income_streams": [],   # [{name, amount, frequency, payday_hint}]
    "buffer_target": 0.0,
    "baseline_notes": "",
}

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        d = dict(DEFAULT)
        d["updated_at"] = _utcnow_iso()
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2)

def get_profile() -> Dict[str, Any]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profile(patch: Dict[str, Any]) -> Dict[str, Any]:
    d = get_profile()
    patch = patch or {}
    for k in ("currency", "income_streams", "buffer_target", "baseline_notes"):
        if k in patch:
            d[k] = patch[k]
    d["updated_at"] = _utcnow_iso()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return d
