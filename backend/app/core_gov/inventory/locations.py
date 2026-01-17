from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "inventory")
PATH = os.path.join(DATA_DIR, "locations.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

DEFAULT = ["pantry", "garage_stock", "deep_freezer", "bathroom", "laundry"]

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "locations": DEFAULT}, f, indent=2)

def get() -> Dict[str, Any]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def add(name: str) -> Dict[str, Any]:
    d = get()
    locs = d.get("locations") or []
    nm = (name or "").strip()
    if nm and nm not in locs:
        locs.append(nm)
    d["locations"] = locs
    d["updated_at"] = _utcnow()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return d
