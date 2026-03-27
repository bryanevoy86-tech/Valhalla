from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta, timezone


def _today() -> str:
    return date.today().isoformat()


def _safe(fn, warnings: List[str], label: str) -> Optional[Any]:
    try:
        return fn()
    except Exception as e:
        warnings.append(f"{label} unavailable: {type(e).__name__}: {e}")
        return None


def _priority_rank(pri: str) -> int:
    ranks = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    return ranks.get(pri, 2)


def feed(days: int = 30) -> Dict[str, Any]:
    """Unified calendar feed merging budget, reminders, followups, shopping."""
    days = max(1, min(120, int(days or 30)))
    warnings: List[str] = []
    items: List[Dict[str, Any]] = []

    # 1. Budget calendar (bills + obligations)
    def _budget():
        from backend.app.core_gov.budget import calendar as cal  # type: ignore
        return (cal.next_n_days_calendar(days) or {}).get("items", [])

    budget_events = _safe(_budget, warnings, "budget_calendar") or []
    for ev in budget_events:
        items.append({
            "date": ev.get("date"),
            "type": ev.get("type"),  # obligation / followup
            "title": ev.get("title"),
            "priority": "high" if not ev.get("autopay_enabled") else "normal",
            "source": "budget",
            "data": ev,
        })

    # 2. Reminders (active or done)
    def _reminders():
        from backend.app.core_gov.reminders import service as rsvc  # type: ignore
        return rsvc.list_items()
    reminder_list = _safe(_reminders, warnings, "reminders") or []
    for rm in reminder_list:
        if rm.get("status") in ("active", "done"):
            items.append({
                "date": rm.get("due_date"),
                "type": "reminder",
                "title": rm.get("title"),
                "priority": rm.get("priority", "normal"),
                "source": rm.get("source"),
                "data": rm,
            })

    # 3. Shopping (open items with desired_by)
    def _shopping():
        from backend.app.core_gov.shopping import service as ssvc  # type: ignore
        return ssvc.list_items(status="open")
    shopping_list = _safe(_shopping, warnings, "shopping") or []
    for sh in shopping_list:
        desired = (sh.get("desired_by") or "").strip()
        if desired:
            items.append({
                "date": desired,
                "type": "shopping",
                "title": f"Buy: {sh.get('name')}",
                "priority": sh.get("priority", "normal"),
                "source": "shopping",
                "data": sh,
            })

    # Filter by date range + sort by priority then date
    today = _today()
    end_date = (date.today() + timedelta(days=days)).isoformat()

    filtered = []
    for it in items:
        evt_date = (it.get("date") or "").strip()
        if evt_date and today <= evt_date <= end_date:
            filtered.append(it)

    filtered.sort(key=lambda x: (
        _priority_rank(x.get("priority", "normal")),
        x.get("date", "9999-99-99"),
    ))

    return {
        "range_days": days,
        "range_start": today,
        "range_end": end_date,
        "warnings": warnings,
        "items": filtered,
    }
