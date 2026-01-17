from __future__ import annotations
from typing import Any, Dict, Tuple

def require_approval(action: str, payload: Dict[str, Any], risk: str = "high") -> Tuple[bool, Dict[str, Any]]:
    """
    Returns (allowed, response).
    If not allowed, it creates an approval request and returns instructions.
    """
    try:
        from backend.app.core_gov.command.mode import get as get_mode  # type: ignore
        mode = (get_mode().get("mode") or "execute").lower()
        if mode == "explore":
            return False, {"ok": False, "error": "Denied in explore mode"}
    except Exception:
        pass

    try:
        from . import store as astore
        # Always require approval for high risk in v1:
        if (risk or "").lower() in ("high","critical"):
            # create approval
            a = {"id": astore.new_id(), "action": action, "payload": payload or {}, "risk": risk, "status": "pending", "created_at": ""}
            from datetime import datetime, timezone
            a["created_at"] = datetime.now(timezone.utc).isoformat()
            items = astore.list_items()
            items.append(a)
            astore.save_items(items)
            return False, {"ok": False, "approval_required": True, "approval": a, "next": f"POST /core/approvals/{a['id']}/approve"}
    except Exception:
        pass

    return True, {"ok": True}
