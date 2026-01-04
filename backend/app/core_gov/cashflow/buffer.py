from __future__ import annotations
from typing import Any, Dict
from .service import forecast

def with_buffer(days: int = 30, buffer_min: float = 500.0) -> Dict[str, Any]:
    fc = forecast(days=days)
    try:
        from backend.app.core_gov.budget.impact import impact  # type: ignore
        bi = impact(buffer_min=buffer_min)
    except Exception:
        bi = {}
    return {"cashflow": fc, "budget_impact": bi}
