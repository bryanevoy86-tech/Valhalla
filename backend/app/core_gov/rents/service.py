from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(property_id: str, gross_rent: float = 0.0, other_income: float = 0.0, expenses_monthly: Dict[str, float] = None, loan_pmt_monthly: float = 0.0, notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    expenses_monthly = expenses_monthly or {}
    meta = meta or {}
    if not (property_id or "").strip():
        raise ValueError("property_id required")

    rec = {
        "id": "rent_" + uuid.uuid4().hex[:12],
        "property_id": property_id.strip(),
        "gross_rent": float(gross_rent or 0.0),
        "other_income": float(other_income or 0.0),
        "expenses_monthly": {k: float(v or 0.0) for k, v in (expenses_monthly or {}).items()},
        "loan_pmt_monthly": float(loan_pmt_monthly or 0.0),
        "notes": notes or "",
        "meta": meta,
        "status": "active",
        "created_at": _utcnow_iso(),
        "updated_at": _utcnow_iso(),
    }
    items = store.list_items()
    items.append(rec)
    store.save_items(items)
    return rec

def _noi(sheet: Dict[str, Any]) -> float:
    inc = float(sheet.get("gross_rent") or 0.0) + float(sheet.get("other_income") or 0.0)
    exp = sum(float(v or 0.0) for v in (sheet.get("expenses_monthly") or {}).values())
    return float(inc - exp)

def dscr(sheet: Dict[str, Any]) -> float:
    debt = float(sheet.get("loan_pmt_monthly") or 0.0)
    if debt <= 0:
        return 0.0
    return float(_noi(sheet) / debt)

def list_by_property(property_id: str) -> List[Dict[str, Any]]:
    items = [x for x in store.list_items() if x.get("property_id") == property_id]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items[:200]

def summarize(property_id: str) -> Dict[str, Any]:
    sheets = list_by_property(property_id)
    out = []
    for s in sheets:
        out.append({
            "rent_id": s.get("id",""),
            "noi_monthly": _noi(s),
            "dscr": dscr(s),
            "gross_rent": float(s.get("gross_rent") or 0.0),
            "loan_pmt_monthly": float(s.get("loan_pmt_monthly") or 0.0),
        })
    return {"property_id": property_id, "items": out}
