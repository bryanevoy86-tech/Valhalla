from __future__ import annotations
from fastapi import APIRouter, Body, HTTPException
from typing import Any, Dict
from .guards import guard
from .actions import dispatch

router = APIRouter(prefix="/core/heimdall", tags=["core-heimdall"])

@router.post("/do")
def do(payload: Dict[str, Any] = Body(...)):
    mode = str((payload or {}).get("mode") or "explore")
    action = str((payload or {}).get("action") or "")
    data = (payload or {}).get("data") or {}

    ok, msg = guard(mode=mode, action=action)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    if mode.lower() == "execute":
        try:
            from backend.app.core_gov.cone.service import decide  # type: ignore
            verdict = decide({"engine":"heimdall_personal_ops", "action": action, "class":"boring"})
            if isinstance(verdict, dict) and verdict.get("allow") is False:
                raise HTTPException(status_code=403, detail=f"cone denied: {verdict.get('reason','blocked')}")
        except HTTPException:
            raise
        except Exception:
            # if cone decide is unavailable, do NOT execute
            raise HTTPException(status_code=503, detail="cone decide unavailable; execute blocked")

    out = dispatch(action=action, payload=data if isinstance(data, dict) else {})
    
    try:
        from backend.app.core_gov.heimdall.log import append  # type: ignore
        append({"mode": mode, "action": action, "data": data})
    except Exception:
        pass
    
    return {"ok": True, "mode": mode, "action": action, "result": out}

@router.post("/plan")
def plan(payload: Dict[str, Any] = Body(...)):
    action = str((payload or {}).get("action") or "")
    data = (payload or {}).get("data") or {}
    # plan is always explore-safe
    out = dispatch(action=action, payload=data if isinstance(data, dict) else {})
    return {"ok": True, "action": action, "plan_result": out}

@router.get("/actions")
def actions(limit: int = 200):
    from backend.app.core_gov.heimdall.log import list_items  # type: ignore
    return {"items": list_items(limit=limit)}
