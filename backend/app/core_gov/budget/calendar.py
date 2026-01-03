from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional


def bill_calendar(start: str, end: str) -> Dict[str, Any]:
    from backend.app.core_gov.obligations import service as oblig_service  # type: ignore

    items = oblig_service.generate_upcoming(start, end)

    # warnings
    warnings: List[str] = []
    for x in items:
        if x.get("autopay_enabled") and not x.get("autopay_verified"):
            warnings.append(f"Autopay not verified: {x.get('name')} due {x.get('due_date')}")

    # shield + coverage
    shield = None
    try:
        from backend.app.core_gov.shield import service as shield_service  # type: ignore
        shield = shield_service.get_config()
    except Exception:
        shield = {"enabled": False}

    if shield and shield.get("enabled"):
        warnings.append(f"Shield is enabled at tier {shield.get('tier', 'green')}.")

    cov = None
    try:
        cov = oblig_service.obligations_status(buffer_multiplier=1.25)
        if cov.get("covered") is False:
            warnings.append("Cash buffer is below 1.25x next-30-days obligations.")
    except Exception:
        cov = None

    # group by due_date
    by_date: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        d = it.get("due_date") or ""
        by_date.setdefault(d, []).append(it)

    days = []
    for d in sorted(by_date.keys()):
        day_total = round(sum(float(x.get("amount") or 0.0) for x in by_date[d]), 2)
        days.append({"date": d, "total": day_total, "items": by_date[d]})

    return {
        "start": start,
        "end": end,
        "days": days,
        "warnings": warnings,
        "coverage": cov,
        "shield": shield,
    }


def next_30_days_calendar() -> Dict[str, Any]:
    s = date.today().isoformat()
    e = (date.today() + timedelta(days=30)).isoformat()
    return bill_calendar(s, e)

