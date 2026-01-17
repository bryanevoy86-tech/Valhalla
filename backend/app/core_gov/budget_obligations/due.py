from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Any, Dict, List
from . import store

def _parse(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()

def _month_last_day(dt: date) -> int:
    nxt = (dt.replace(day=28) + timedelta(days=4)).replace(day=1)
    return (nxt - timedelta(days=1)).day

def upcoming(days: int = 14, today: str = "") -> Dict[str, Any]:
    days = max(1, min(120, int(days or 14)))
    now = _parse(today) if today else date.today()
    end = now + timedelta(days=days)

    items = [x for x in store.list_items() if x.get("status") == "active"]
    due: List[Dict[str, Any]] = []

    for ob in items:
        freq = ob.get("frequency")
        amt = float(ob.get("amount") or 0.0)

        if freq == "one_time":
            dd = (ob.get("due_date") or "").strip()
            if dd:
                ddt = _parse(dd)
                if now <= ddt <= end:
                    due.append({"obligation": ob, "due_date": dd, "amount": amt})
            continue

        due_day = int(ob.get("due_day") or 1)
        due_day = min(max(due_day, 1), _month_last_day(now))
        candidate = now.replace(day=due_day)
        if candidate < now:
            y = now.year + (1 if now.month == 12 else 0)
            m = 1 if now.month == 12 else now.month + 1
            first = date(y, m, 1)
            due_day2 = min(due_day, _month_last_day(first))
            candidate = first.replace(day=due_day2)

        if now <= candidate <= end:
            due.append({"obligation": ob, "due_date": candidate.isoformat(), "amount": amt})

    due.sort(key=lambda x: x.get("due_date",""))
    total = round(sum(float(x.get("amount") or 0.0) for x in due), 2)
    return {"from": now.isoformat(), "to": end.isoformat(), "count": len(due), "total_amount": total, "items": due}
