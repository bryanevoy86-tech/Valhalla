from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone, date, timedelta
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "assets")
PATH = os.path.join(DATA_DIR, "replace.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "items": []}, f, indent=2)

def new_id() -> str:
    return "rep_" + uuid.uuid4().hex[:12]

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

def add(title: str, within_days: int = 60, est_cost: float = 0.0, notes: str = "") -> Dict[str, Any]:
    due = (date.today() + timedelta(days=max(1, int(within_days or 60)))).isoformat()
    rec = {"id": new_id(), "title": title, "due": due, "est_cost": float(est_cost or 0.0), "notes": notes or "", "status":"open", "created_at": _utcnow(), "updated_at": _utcnow()}
    items = list_items()
    items.append(rec)
    save_items(items)
    return rec
