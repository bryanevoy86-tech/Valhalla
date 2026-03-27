from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict

DATA_DIR = os.path.join("backend", "data", "know_citations")
PATH = os.path.join(DATA_DIR, "map.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "map": {}}, f, indent=2)

def get() -> Dict[str, Any]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def link(chunk_id: str, source_id: str) -> Dict[str, Any]:
    d = get()
    mp = d.get("map") or {}
    mp[str(chunk_id)] = str(source_id)
    d["map"] = mp
    d["updated_at"] = _utcnow()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
    return d
