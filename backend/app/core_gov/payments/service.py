from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Dict, List
from backend.app.core_gov.due_dates.service import next_due

def compute_next(p: Dict[str, Any], from_date: str = "") -> str:
    if (p.get("next_due_override") or "").strip():
        return str(p.get("next_due_override"))
    return next_due(
        cadence=str(p.get("cadence") or "monthly"),
        due_day=int(p.get("due_day") or 1),
        from_date=from_date,
    )

def schedule(items: List[Dict[str, Any]], days: int = 30) -> List[Dict[str, Any]]:
    days = max(7, min(180, int(days or 30)))
    start = date.today()
    end = start + timedelta(days=days)
    out: List[Dict[str, Any]] = []

    for p in items:
        if p.get("status") != "active":
            continue
        nd = compute_next(p, from_date=start.isoformat())
        try:
            d = date.fromisoformat(nd)
        except Exception:
            continue
        if start <= d <= end:
            out.append({
                "date": nd,
                "payment_id": p.get("id"),
                "name": p.get("name"),
                "kind": p.get("kind"),
                "amount": p.get("amount"),
                "currency": p.get("currency"),
                "autopay_enabled": bool(p.get("autopay_enabled")),
                "autopay_verified": bool(p.get("autopay_verified")),
            })

    out.sort(key=lambda x: x.get("date", ""))
    return out
