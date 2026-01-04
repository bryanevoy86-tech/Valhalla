from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Dict, List, Tuple
from . import store

def log_usage(inv_id: str, qty_used: float, used_on: str = "", notes: str = "") -> Dict[str, Any]:
    used_on = (used_on or date.today().isoformat()).strip()
    rec = {
        "id": store.new_id(),
        "inv_id": inv_id,
        "qty_used": float(qty_used or 0.0),
        "used_on": used_on,
        "notes": notes or "",
        "created_at": store._utcnow(),  # type: ignore
    }
    ev = store.list_events()
    ev.append(rec)
    store.save_events(ev)
    return rec

def burn_rate(inv_id: str, window_days: int = 30) -> Dict[str, Any]:
    window_days = max(7, min(365, int(window_days or 30)))
    cutoff = date.today() - timedelta(days=window_days)
    ev = [e for e in store.list_events() if e.get("inv_id") == inv_id and (e.get("used_on") or "") >= cutoff.isoformat()]
    total_used = sum(float(e.get("qty_used") or 0.0) for e in ev)
    per_day = total_used / float(window_days) if window_days else 0.0
    return {"inv_id": inv_id, "window_days": window_days, "total_used": round(total_used, 3), "per_day": round(per_day, 5)}

def forecast_days_left(inv_item: Dict[str, Any], window_days: int = 30) -> Dict[str, Any]:
    inv_id = inv_item.get("id")
    qty = float(inv_item.get("qty") or 0.0)
    br = burn_rate(inv_id=inv_id, window_days=window_days)
    per_day = float(br.get("per_day") or 0.0)
    days_left = (qty / per_day) if per_day > 0 else None
    return {**br, "qty_now": qty, "days_left": (round(days_left, 1) if days_left is not None else None)}
