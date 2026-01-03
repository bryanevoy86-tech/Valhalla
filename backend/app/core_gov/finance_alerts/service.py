from __future__ import annotations

from datetime import date
from typing import Any, Dict, List


def run_checks(unreconciled_threshold: int = 25) -> Dict[str, Any]:
    warnings: List[str] = []
    alerts: List[Dict[str, Any]] = []

    today = date.today().isoformat()

    # unreconciled bank txns
    try:
        from backend.app.core_gov.bank import service as bsvc  # type: ignore
        cnt = len(bsvc.list_txns(status="new", limit=1000))
        if cnt >= int(unreconciled_threshold or 25):
            alerts.append({"type": "bank_unreconciled", "severity": "high", "title": "Bank txns need reconciliation", "detail": f"{cnt} unreconciled txns"})
    except Exception as e:
        warnings.append(f"bank unavailable: {type(e).__name__}: {e}")

    # reminders due today/overdue (string compare works for ISO dates)
    try:
        from backend.app.core_gov.reminders import service as rsvc  # type: ignore
        rms = rsvc.list_items(status="active")
        due = [r for r in rms if (r.get("due_date") or "") <= today]
        if due:
            alerts.append({"type": "reminders_due", "severity": "critical", "title": "Reminders due/overdue", "detail": f"{len(due)} reminders need action", "items": due[:10]})
    except Exception as e:
        warnings.append(f"reminders unavailable: {type(e).__name__}: {e}")

    # bills due soon without autopay
    try:
        from backend.app.core_gov.budget import calendar as cal  # type: ignore
        ev = cal.next_n_days_calendar(3)
        items = (ev or {}).get("items", []) if isinstance(ev, dict) else (ev or [])
        risky = [x for x in items if x.get("type") == "obligation" and not x.get("autopay_enabled")]
        if risky:
            alerts.append({"type": "bills_due_soon", "severity": "high", "title": "Bills due soon (manual)", "detail": f"{len(risky)} bills due within 3 days", "items": risky[:10]})
    except Exception as e:
        warnings.append(f"budget_calendar unavailable: {type(e).__name__}: {e}")

    # optionally push into existing alerts module if present
    pushed = 0
    try:
        from backend.app.alerts import store as astore  # type: ignore
        for a in alerts:
            astore.add_alert(a)  # if your alerts store has a different signature, it will just be skipped by exception
            pushed += 1
    except Exception:
        pass

    return {"today": today, "alerts": alerts, "pushed_to_alerts_module": pushed, "warnings": warnings}
