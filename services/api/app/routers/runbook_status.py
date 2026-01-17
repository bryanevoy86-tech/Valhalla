from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.go_live import checklist, read_state
from app.services.engine_state import list_states

router = APIRouter(prefix="/api/runbook", tags=["Governance", "Runbook"])


@router.get("/status")
def runbook_status(db: Session = Depends(get_db)):
    """
    Fail-safe runbook status. Never 500.
    """
    try:
        go = read_state(db)
        cl = checklist(db)
        engines = list_states(db)

        blockers = []
        if not cl.get("ok", False):
            # Flatten required checks that are not ok
            required = cl.get("required", {})
            for k, v in required.items():
                if not v.get("ok", False):
                    blockers.append({"code": k, "detail": v.get("detail")})

        # If kill switch engaged => always blocked
        if getattr(go, "kill_switch_engaged", False):
            blockers.append({"code": "kill_switch_engaged", "detail": "Kill switch engaged"})

        return {
            "ok": len(blockers) == 0,
            "blockers": blockers,
            "warnings": cl.get("warnings", {}),
            "go_live": {
                "enabled": bool(getattr(go, "go_live_enabled", False)),
                "kill_switch_engaged": bool(getattr(go, "kill_switch_engaged", False)),
                "changed_by": getattr(go, "changed_by", None),
                "reason": getattr(go, "reason", None),
                "updated_at": getattr(go, "updated_at", None).isoformat() if getattr(go, "updated_at", None) else None,
            },
            "engines": engines,
        }
    except Exception as e:
        # Fail-safe degradation (never 500)
        return {
            "ok": False,
            "blockers": [{"code": "runbook_exception", "detail": str(e)}],
            "warnings": {},
            "go_live": {},
            "engines": [],
        }
