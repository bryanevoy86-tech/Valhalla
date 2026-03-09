from __future__ import annotations
from typing import Any, Dict

def check_and_trigger(buffer_min: float = 500.0) -> Dict[str, Any]:
    # if budget impact reports "at_risk", trigger
    try:
        from backend.app.core_gov.budget.impact import impact  # type: ignore
        bi = impact(buffer_min=buffer_min)
    except Exception:
        return {"ok": False, "error": "budget.impact unavailable"}

    at_risk = bool(bi.get("at_risk"))
    if not at_risk:
        return {"ok": True, "triggered": False, "budget_impact": bi}

    try:
        from backend.app.core_gov.shield_lite.service import activate  # type: ignore
        out = activate(reason="buffer risk", notes=str(bi))
        return {"ok": True, "triggered": True, "activated": out, "budget_impact": bi}
    except Exception as e:
        return {"ok": False, "error": f"activate failed: {type(e).__name__}: {e}", "budget_impact": bi}
