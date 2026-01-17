from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from . import store

def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def create(property_id: str, title: str = "Repair Worksheet", line_items: List[Dict[str, Any]] = None, notes: str = "", meta: Dict[str, Any] = None) -> Dict[str, Any]:
    line_items = line_items or []
    meta = meta or {}
    if not (property_id or "").strip():
        raise ValueError("property_id required")

    rec = {
        "id": "rep_" + uuid.uuid4().hex[:12],
        "property_id": property_id.strip(),
        "title": title or "Repair Worksheet",
        "line_items": line_items,  # {category, item, qty, unit_cost, labor_cost, notes}
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

def list_by_property(property_id: str) -> List[Dict[str, Any]]:
    items = [x for x in store.list_items() if x.get("property_id") == property_id]
    items.sort(key=lambda x: x.get("updated_at",""), reverse=True)
    return items[:200]

def total_cost(sheet: Dict[str, Any]) -> float:
    total = 0.0
    for li in (sheet.get("line_items") or []):
        qty = float(li.get("qty") or 0.0)
        unit = float(li.get("unit_cost") or 0.0)
        labor = float(li.get("labor_cost") or 0.0)
        total += qty * unit + labor
    return float(total)

def summarize(property_id: str) -> Dict[str, Any]:
    sheets = list_by_property(property_id)
    totals = [{"repair_id": s.get("id",""), "title": s.get("title",""), "total": total_cost(s)} for s in sheets]
    grand = sum(x["total"] for x in totals)
    return {"property_id": property_id, "sheets": totals, "grand_total": float(grand)}
