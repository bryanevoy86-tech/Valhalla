from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "balance_snapshots")
PATH = os.path.join(DATA_DIR, "items.json")

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow_iso(), "items": []}, f, indent=2)

def list_items() -> List[Dict[str, Any]]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

def save_items(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow_iso(), "items": items[-50000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)

def new_id() -> str:
    return "bal_" + uuid.uuid4().hex[:12]
