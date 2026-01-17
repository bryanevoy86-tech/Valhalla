from __future__ import annotations
from typing import Any, Dict

def monthly_plan(month: str) -> Dict[str, Any]:
    # month = YYYY-MM; v1 is approximate totals
    obligations_total = 0.0
    try:
        from backend.app.core_gov.budget_obligations import store as obstore  # type: ignore
        obs = [x for x in obstore.list_items() if x.get("status") == "active"]
        for ob in obs:
            obligations_total += float(ob.get("amount") or 0.0)
    except Exception:
        pass

    buffer = 0.0
    income = 0.0
    currency = "CAD"
    try:
        from backend.app.core_gov.house_budget import store as hbstore  # type: ignore
        p = hbstore.get_profile()
        currency = p.get("currency") or "CAD"
        buffer = float(p.get("buffer_target") or 0.0)
        for s in (p.get("income_streams") or []):
            income += float(s.get("amount") or 0.0)
    except Exception:
        pass

    need = round(obligations_total + buffer, 2)
    income = round(income, 2)
    gap = round(need - income, 2)
    return {
        "month": month,
        "currency": currency,
        "obligations_estimate": round(obligations_total, 2),
        "buffer_target": round(buffer, 2),
        "income_reference": income,
        "need": need,
        "gap": gap,
    }
