from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(
    name: str,
    amount: float,
    cadence: str,
    due_day: int = 1,
    due_months: int = 1,
    start_date: str = "",
    pay_to: str = "",
    category: str = "household",
    account_hint: str = "",
    autopay_status: str = "unknown",
    notes: str = "",
    meta: Dict[str, Any] = None,
    status: str = "active",
) -> Dict[str, Any]:
    meta = meta or {}
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    if float(amount or 0.0) < 0:
        raise ValueError("amount must be >= 0")
    cadence = (cadence or "").strip().lower()
    if cadence not in ("monthly","weekly","quarterly","yearly","custom_months"):
        raise ValueError("cadence must be monthly|weekly|quarterly|yearly|custom_months")

    due_day = int(due_day or 1)
    if cadence == "monthly":
        due_day = max(1, min(due_day, 28))
        due_months = 1
    elif cadence == "weekly":
        due_day = max(0, min(due_day, 6))
        due_months = 0
    elif cadence == "quarterly":
        due_day = max(1, min(due_day, 28))
        due_months = 3
    elif cadence == "yearly":
        due_day = max(1, min(due_day, 28))
        due_months = 12
    else:
        due_day = max(1, min(due_day, 28))
        due_months = max(1, min(int(due_months or 1), 24))

    rec = {
        "id": "obl_" + uuid.uuid4().hex[:12],
        "name": name,
        "amount": float(amount or 0.0),
        "cadence": cadence,
        "due_day": due_day,
        "due_months": due_months,
        "start_date": (start_date or "").strip(),
        "pay_to": (pay_to or "").strip(),
        "category": (category or "household").strip(),
        "account_hint": (account_hint or "").strip(),
        "autopay_status": (autopay_status or "unknown").strip(),
        "status": status or "active",
        "notes": notes or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def list_items(status: str = "", category: str = "", q: str = "") -> List[Dict[str, Any]]:
    items = store.list_items()
    if status:
        items = [x for x in items if x.get("status") == status]
    if category:
        items = [x for x in items if x.get("category") == category]
    if q:
        qq = q.strip().lower()
        items = [x for x in items if qq in (x.get("name","").lower()) or qq in (x.get("pay_to","").lower()) or qq in (x.get("notes","").lower())]
    items.sort(key=lambda x: x.get("name",""))
    return items[:2000]

def get_one(obligation_id: str) -> Optional[Dict[str, Any]]:
    for x in store.list_items():
        if x.get("id") == obligation_id:
            return x
    return None
