from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "routines")
PATH = os.path.join(DATA_DIR, "routines.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "items": []}, f, indent=2)

def new_id() -> str:
    return "rt_" + uuid.uuid4().hex[:12]

def list_items() -> List[Dict[str, Any]]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

def save_items(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow(), "items": items[-200000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)

def create(title: str, freq: str = "weekly", day_of_week: str = "mon", items: List[str] | None = None, notes: str = "") -> Dict[str, Any]:
    t = (title or "").strip()
    if not t:
        raise ValueError("title required")
    rec = {
        "id": new_id(),
        "title": t,
        "freq": (freq or "weekly").lower(),
        "day_of_week": (day_of_week or "mon").lower(),
        "items": items or [],
        "notes": notes or "",
        "status": "active",
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    arr = list_items()
    arr.append(rec)
    save_items(arr)
    return rec
