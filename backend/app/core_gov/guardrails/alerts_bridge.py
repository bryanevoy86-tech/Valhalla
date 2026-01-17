from __future__ import annotations

from typing import Any, Dict, List
from . import service as guard

def run_and_alert(days_ahead: int = 7) -> Dict[str, Any]:
    res = guard.daily_guard(days_ahead=days_ahead)
    warnings: List[str] = res.get("warnings") or []

    alerts = []
    if res.get("bills_due"):
        alerts.append({"level": "info", "title": "Bills Due", "detail": f"{len(res['bills_due'])} bill(s) due soon."})
    buf = res.get("buffer") or {}
    req = float(buf.get("required") or 0.0)
    if req > 0:
        alerts.append({"level": "warning", "title": "Bills Buffer Required", "detail": f"Target buffer for 30 days: {req:.2f}"})
    if res.get("low_stock"):
        alerts.append({"level": "warning", "title": "Low Stock", "detail": f"{len(res['low_stock'])} item(s) low."})

    pushed = 0
    try:
        from backend.app.alerts import store as astore  # type: ignore
        for a in alerts:
            try:
                astore.create_alert({"type": "guardrail", "level": a["level"], "title": a["title"], "message": a["detail"]})
                pushed += 1
            except Exception:
                break
    except Exception as e:
        warnings.append(f"alerts module not available (safe): {type(e).__name__}: {e}")

    res["alerts_preview"] = alerts
    res["alerts_pushed"] = pushed
    res["warnings"] = warnings
    return res
