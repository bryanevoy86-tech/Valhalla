from __future__ import annotations
import json, os
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "heimdall")
PATH = os.path.join(DATA_DIR, "actions.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "items": []}, f, indent=2)

def list_items(limit: int = 200) -> List[Dict[str, Any]]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        items = json.load(f).get("items", [])
    items.sort(key=lambda x: x.get("ts",""), reverse=True)
    return items[:max(1, min(5000, int(limit or 200)))]

def append(rec: Dict[str, Any]) -> None:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        d = json.load(f)
    items = d.get("items", [])
    items.append({**rec, "ts": _utcnow()})
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow(), "items": items[-200000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)
