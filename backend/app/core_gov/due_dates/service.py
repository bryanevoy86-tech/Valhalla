from __future__ import annotations
from datetime import date, timedelta
from typing import Optional

def _today() -> date:
    return date.today()

def _clamp_dom(dom: int) -> int:
    return 1 if dom < 1 else 31 if dom > 31 else dom

def _safe_date(y: int, m: int, d: int) -> date:
    # avoid month-length edge cases by clamping to 28 then stepping forward
    d = min(max(1, d), 28)
    return date(y, m, d)

def _add_months(base: date, months: int) -> date:
    y = base.year + (base.month - 1 + months) // 12
    m = (base.month - 1 + months) % 12 + 1
    return _safe_date(y, m, base.day)

def next_due(cadence: str, due_day: int = 1, from_date: str = "") -> str:
    """
    cadence: once|weekly|biweekly|monthly|quarterly|yearly
    due_day:
      - weekly/biweekly: ignored (uses 7/14 days)
      - monthly/quarterly/yearly: day-of-month (1..31), clamped
    from_date: ISO YYYY-MM-DD; defaults to today
    """
    cadence = (cadence or "monthly").strip().lower()
    d0 = _today()
    if from_date:
        try:
            d0 = date.fromisoformat(from_date)
        except Exception:
            d0 = _today()

    dom = _clamp_dom(int(due_day or 1))

    if cadence in ("weekly",):
        return (d0 + timedelta(days=7)).isoformat()
    if cadence in ("biweekly", "bi-weekly"):
        return (d0 + timedelta(days=14)).isoformat()
    if cadence in ("once", "single"):
        return d0.isoformat()

    # monthly/quarterly/yearly use day-of-month
    # Build candidate date in current month on dom (clamped to <=28 to stay safe)
    cand = _safe_date(d0.year, d0.month, dom)

    if cand < d0:
        # move forward by cadence period
        if cadence == "monthly":
            cand = _add_months(cand, 1)
        elif cadence == "quarterly":
            cand = _add_months(cand, 3)
        elif cadence == "yearly":
            cand = _add_months(cand, 12)
        else:
            cand = _add_months(cand, 1)

    # keep dom intent by reapplying day (still safe/clamped)
    cand = _safe_date(cand.year, cand.month, dom)
    return cand.isoformat()
