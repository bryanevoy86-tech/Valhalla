from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "pay_confirm")
PATH = os.path.join(DATA_DIR, "confirmations.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "items": []}, f, indent=2)

def new_id() -> str:
    return "pc_" + uuid.uuid4().hex[:12]

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

def create(payment_id: str, paid_on: str, amount: float, currency: str = "CAD", method: str = "", ref: str = "", notes: str = "") -> Dict[str, Any]:
    rec = {
        "id": new_id(),
        "payment_id": payment_id,
        "paid_on": paid_on,
        "amount": float(amount or 0.0),
        "currency": (currency or "CAD").strip().upper(),
        "method": method or "",
        "ref": ref or "",
        "notes": notes or "",
        "created_at": _utcnow(),
    }
    items = list_items()
    items.append(rec)
    save_items(items)
    return rec
