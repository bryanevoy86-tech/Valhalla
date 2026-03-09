from __future__ import annotations
from typing import Any, Dict, List
from .snapshot import snapshot

def check(buffer_min: float = 500.0) -> Dict[str, Any]:
    s = snapshot()
    income_target = float((s.get("budget") or {}).get("month_income_target") or 0.0)
    bills = float(s.get("bills_monthly_est") or 0.0)
    buffer_min = float(buffer_min or 0.0)
    projected = income_target - bills - buffer_min

    alert = None
    if income_target > 0 and projected < 0:
        alert = {"type": "budget", "severity": "warning", "title": "Budget buffer risk", "detail": f"Projected negative after buffer: {round(projected,2)}"}

        try:
            from backend.app.alerts import store as astore  # type: ignore
            astore.create_alert(alert)
        except Exception:
            pass

    return {"income_target": income_target, "bills_monthly_est": bills, "buffer_min": buffer_min, "projected_after_buffer": round(projected, 2), "alert": alert}
