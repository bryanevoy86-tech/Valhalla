from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

DATA_DIR = os.path.join("backend", "data", "payments")
PATH = os.path.join(DATA_DIR, "payments.json")

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(PATH):
        with open(PATH, "w", encoding="utf-8") as f:
            json.dump({"updated_at": _utcnow(), "items": []}, f, indent=2)

def new_id() -> str:
    return "pay_" + uuid.uuid4().hex[:12]

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

def create(
    name: str,
    amount: float,
    cadence: str = "monthly",
    currency: str = "CAD",
    due_day: int = 1,
    kind: str = "bill",
    payee: str = "",
    autopay_enabled: bool = False,
    autopay_verified: bool = False,
    account_id: str = "",
    notes: str = "",
    status: str = "active",
) -> Dict[str, Any]:
    nm = (name or "").strip()
    if not nm:
        raise ValueError("name required")
    rec = {
        "id": new_id(),
        "name": nm,
        "kind": (kind or "bill").strip().lower(),   # bill|subscription|other
        "payee": payee or "",
        "amount": float(amount or 0.0),
        "currency": (currency or "CAD").strip().upper(),
        "cadence": (cadence or "monthly").strip().lower(),
        "due_day": int(due_day or 1),
        "next_due_override": "",  # ISO date if you want to pin it
        "autopay_enabled": bool(autopay_enabled),
        "autopay_verified": bool(autopay_verified),
        "account_id": account_id or "",
        "notes": notes or "",
        "status": status or "active",  # active|paused|cancelled
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    items = list_items()
    items.append(rec)
    save_items(items)
    return rec
