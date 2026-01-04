from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone, date
from typing import Any, Dict, List
from . import store as bstore
from .due import upcoming

DATA_DIR = os.path.join("backend", "data", "bills")
PATH = os.path.join(DATA_DIR, "pay_log.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "items": []}, f, indent=2)

def list_items() -> List[Dict[str, Any]]:
    _ensure()
    with open(PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("items", [])

def save_items(items: List[Dict[str, Any]]) -> None:
    _ensure()
    tmp = PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"updated_at": _utcnow(), "items": items[-100000:]}, f, indent=2, ensure_ascii=False)
    os.replace(tmp, PATH)

def mark_paid(bill_id: str, paid_on: str = "", amount: float = 0.0, notes: str = "") -> Dict[str, Any]:
    bills = bstore.list_bills()
    b = next((x for x in bills if x.get("id") == bill_id), None)
    if not b:
        raise KeyError("bill not found")
    rec = {
        "id": "pay_" + uuid.uuid4().hex[:12],
        "bill_id": bill_id,
        "name": b.get("name"),
        "paid_on": paid_on or date.today().isoformat(),
        "amount": float(amount or b.get("amount") or 0.0),
        "notes": notes or "",
        "created_at": _utcnow(),
    }
    items = list_items()
    items.append(rec)
    save_items(items)
    return rec

def missed() -> Dict[str, Any]:
    # v1: show bills whose next_due is in past AND no payment logged on/after that due within 7 days
    up = upcoming(limit=500).get("upcoming") or []
    logs = list_items()
    out = []
    today = date.today().isoformat()
    for b in up:
        due = b.get("next_due") or ""
        if not due or due >= today:
            continue
        # find any payment for this bill_id within last 14 days
        bill_id = b.get("id")
        paid = [x for x in logs if x.get("bill_id") == bill_id]
        out.append({"bill_id": bill_id, "name": b.get("name"), "due": due, "payments": paid[-3:]})
    return {"missed": out[:200]}
