from __future__ import annotations
from typing import Any, Dict, List
from . import store

def activate(reason: str, notes: str = "") -> Dict[str, Any]:
    s = store.get_state()
    if not s.get("enabled"):
        return {"ok": False, "error": "shield_lite disabled"}
    s["active"] = True
    s["reason"] = reason or "risk"
    s["notes"] = notes or ""
    s["triggered_at"] = store._utcnow()  # type: ignore
    store.set_state(s)
    _best_effort_alert(f"Shield Lite ACTIVATED: {s['reason']}")
    return {"ok": True, "state": s}

def deactivate(notes: str = "") -> Dict[str, Any]:
    s = store.get_state()
    s["active"] = False
    s["reason"] = ""
    s["notes"] = notes or ""
    store.set_state(s)
    _best_effort_alert("Shield Lite DEACTIVATED")
    return {"ok": True, "state": s}

def _best_effort_alert(msg: str) -> None:
    try:
        from backend.app.core_gov.alerts import store as astore  # type: ignore
        if hasattr(astore, "create"):
            astore.create(title=msg, kind="shield", severity="high", notes=msg)  # type: ignore
            return
    except Exception:
        pass
    try:
        from backend.app.core_gov.reminders import service as rsvc  # type: ignore
        rsvc.create(title=msg, due_date="", kind="shield", notes=msg)
    except Exception:
        pass
