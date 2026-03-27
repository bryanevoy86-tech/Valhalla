from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "credit")
PATH = os.path.join(DATA_DIR, "tradelines.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "items": []}, f, indent=2)

def new_id() -> str:
    return "tl_" + uuid.uuid4().hex[:12]

def list_items() -> List[Dict[str, Any]]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

def save_items(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow(), "items": items[-20000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)

def add(vendor: str, tier: str = "net30", status: str = "todo", notes: str = "") -> Dict[str, Any]:
    vendor = (vendor or "").strip()
    if not vendor:
        raise ValueError("vendor required")
    rec = {"id": new_id(), "vendor": vendor, "tier": (tier or "net30").lower(), "status": (status or "todo").lower(), "notes": notes or "", "created_at": _utcnow(), "updated_at": _utcnow()}
    items = list_items()
    items.append(rec)
    save_items(items)
    return rec
