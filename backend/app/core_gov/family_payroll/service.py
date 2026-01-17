from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def add_person(name: str, role: str = "child", status: str = "active", notes: str = "") -> Dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("name required")
    rec = {"id": "fp_" + uuid.uuid4().hex[:12], "name": name, "role": role, "status": status, "notes": notes or "", "created_at": _utcnow_iso()}
    ppl = store.list_people()
    ppl.append(rec)
    store.save_people(ppl)
    return rec

def list_people(status: str = "") -> List[Dict[str, Any]]:
    ppl = store.list_people()
    if status:
        ppl = [x for x in ppl if x.get("status") == status]
    ppl.sort(key=lambda x: x.get("name",""))
    return ppl

def add_entry(person_id: str, entry_type: str, date: str, amount: float = 0.0, description: str = "", deduction_type: str = "", meal_log: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    meta = meta or {}
    if not person_id:
        raise ValueError("person_id required")
    if not date:
        raise ValueError("date required YYYY-MM-DD")
    if entry_type not in ("task", "pay", "deduction", "meal"):
        raise ValueError("entry_type must be task|pay|deduction|meal")

    rec = {
        "id": "fe_" + uuid.uuid4().hex[:12],
        "person_id": person_id,
        "entry_type": entry_type,
        "date": date,
        "amount": float(amount or 0.0),
        "description": description or "",
        "deduction_type": deduction_type or "",
        "meal_log": meal_log or "",
        "meta": meta,
        "created_at": _utcnow_iso(),
    }
    items = store.list_entries()
    items.append(rec)
    store.save_entries(items)
    return rec

def list_entries(person_id: str = "", entry_type: str = "", date_from: str = "", date_to: str = "") -> List[Dict[str, Any]]:
    items = store.list_entries()
    if person_id:
        items = [x for x in items if x.get("person_id") == person_id]
    if entry_type:
        items = [x for x in items if x.get("entry_type") == entry_type]
    if date_from:
        items = [x for x in items if (x.get("date") or "") >= date_from]
    if date_to:
        items = [x for x in items if (x.get("date") or "") <= date_to]
    items.sort(key=lambda x: x.get("date",""), reverse=True)
    return items[:500]

def cra_warnings_stub(person_id: str = "", year: int = 0) -> Dict[str, Any]:
    # Placeholder: real CRA threshold logic later.
    warnings = []
    if year and year < 2000:
        warnings.append("year looks invalid")
    warnings.append("CRA limits/wage reasonableness checks are stubbed (placeholder).")
    return {"person_id": person_id, "year": int(year or 0), "warnings": warnings}
