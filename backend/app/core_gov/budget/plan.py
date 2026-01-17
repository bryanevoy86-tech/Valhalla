from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from . import store


def _ym_today() -> str:
    t = date.today()
    return f"{t.year:04d}-{t.month:02d}"


def _parse_ym(ym: str) -> tuple:
    if not ym:
        ym = _ym_today()
    parts = ym.split("-")
    if len(parts) != 2:
        raise ValueError("month must be YYYY-MM")
    y = int(parts[0])
    m = int(parts[1])
    if m < 1 or m > 12:
        raise ValueError("month must be YYYY-MM")
    return y, m


def month_plan_view(month: str) -> Dict[str, Any]:
    y, m = _parse_ym(month)
    obligations = [o for o in store.list_obligations() if o.get("status") == "active"]
    expected: List[Dict[str, Any]] = []
    total = 0.0

    for ob in obligations:
        cad = ob.get("cadence") or "monthly"
        dd = int(ob.get("due_day") or 1)
        due_months = ob.get("due_months") or []

        applies = False
        if cad == "monthly":
            applies = (not due_months) or (m in due_months)
        elif cad == "quarterly":
            applies = (m in due_months) if due_months else (m in (1, 4, 7, 10))
        elif cad == "yearly":
            applies = (m in due_months) if due_months else (m == 1)
        elif cad in ("weekly", "biweekly"):
            applies = True  # we treat weekly/biweekly as ongoing; amount is per occurrence; v1 keeps as-is
        elif cad == "one_time":
            meta = ob.get("meta") or {}
            dt = meta.get("one_time_date") or ""
            try:
                oy, om, _ = dt.split("-")
                applies = (int(oy) == y and int(om) == m)
            except Exception:
                applies = False

        if not applies:
            continue

        amt = float(ob.get("amount") or 0.0)
        total += amt
        expected.append({
            "obligation_id": ob.get("id"),
            "name": ob.get("name"),
            "category": ob.get("category"),
            "amount": amt,
            "currency": ob.get("currency") or "CAD",
            "cadence": cad,
            "due_day": dd,
            "autopay_enabled": bool(ob.get("autopay_enabled") or False),
            "method": ob.get("method") or "manual",
        })

    expected.sort(key=lambda x: (x.get("due_day", 1), -float(x.get("amount") or 0.0)))
    return {"month": f"{y:04d}-{m:02d}", "expected_total": float(total), "items": expected}


def obligations_status(buffer_multiplier: float = 1.25) -> Dict[str, Any]:
    obligations = [o for o in store.list_obligations() if o.get("status") == "active"]
    monthly_total = 0.0

    for ob in obligations:
        cad = ob.get("cadence") or "monthly"
        amt = float(ob.get("amount") or 0.0)
        # normalize to monthly estimate
        if cad == "monthly":
            monthly_total += amt
        elif cad == "quarterly":
            monthly_total += (amt / 3.0)
        elif cad == "yearly":
            monthly_total += (amt / 12.0)
        elif cad == "weekly":
            monthly_total += (amt * 4.0)
        elif cad == "biweekly":
            monthly_total += (amt * 2.0)
        elif cad == "one_time":
            # ignore in monthly baseline
            pass

    buffered = float(monthly_total) * float(buffer_multiplier or 1.25)
    return {
        "active_obligations": len(obligations),
        "monthly_estimated_total": float(monthly_total),
        "buffer_multiplier": float(buffer_multiplier or 1.25),
        "monthly_buffered_target": float(buffered),
        "note": "This is a planning target. Execution (bank autopay) is guidance-only in v1.",
    }
