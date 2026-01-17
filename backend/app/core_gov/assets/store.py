from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "assets")
PATH = os.path.join(DATA_DIR, "assets.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "items": []}, f, indent=2)

def new_id() -> str:
    return "ast_" + uuid.uuid4().hex[:12]

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

def create(name: str, kind: str = "household", purchase_date: str = "", purchase_price: float = 0.0, warranty_months: int = 0, serial: str = "", location: str = "", notes: str = "") -> Dict[str, Any]:
    nm = (name or "").strip()
    if not nm:
        raise ValueError("name required")
    rec = {
        "id": new_id(),
        "name": nm,
        "kind": kind or "household",
        "purchase_date": purchase_date or "",
        "purchase_price": float(purchase_price or 0.0),
        "warranty_months": int(warranty_months or 0),
        "serial": serial or "",
        "location": location or "",
        "notes": notes or "",
        "status": "active",  # active|sold|disposed
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    items = list_items()
    items.append(rec)
    save_items(items)
    return rec
