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

@router.post("/capture")
def capture(payload: Dict[str, Any] = Body(...)):
    """
    One-liner input like:
    - "internet 150 paid on the 15th"
    - "rent 1500 paid on the 1st"
    - "running low on milk"
    Returns candidate + optional best-effort create.
    """
    text = str((payload or {}).get("text") or "")
    mode = str((payload or {}).get("mode") or "explore").lower()

    from backend.app.core_gov.nlp.intent import intent  # type: ignore
    it = intent(text=text)
    if not it.get("ok"):
        return it

    created = None
    # only create in execute mode
    if mode == "execute":
        try:
            # cone gate
            from backend.app.core_gov.cone.service import decide  # type: ignore
            verdict = decide({"engine":"heimdall_personal_ops", "action": f"capture:{it.get('intent')}", "class":"boring"})
            if isinstance(verdict, dict) and verdict.get("allow") is False:
                return {"ok": False, "error": f"cone denied: {verdict.get('reason','blocked')}", "intent": it}
        except Exception:
            return {"ok": False, "error": "cone decide unavailable; execute blocked", "intent": it}

        try:
            if it.get("intent") == "bill.create_candidate":
                from backend.app.core_gov.bills.nlp_intake import create_from_candidate  # type: ignore
                created = create_from_candidate(it.get("candidate") or {})
            elif it.get("intent") == "shopping.quick_add_candidate":
                from backend.app.core_gov.shopping.store import add  # type: ignore
                c = it.get("candidate") or {}
                created = add(name=str(c.get("name") or ""), qty=1.0, unit="each", category=str(c.get("category") or "household"), est_unit_cost=float(c.get("est_total") or 0.0), source="manual", ref_id="", notes=str(c.get("notes") or ""))
            elif it.get("intent") == "schedule.create_candidate":
                from backend.app.core_gov.schedule.router import create as create_event  # type: ignore
                c = it.get("candidate") or {}
                created = create_event(title=str(c.get("title") or ""), date=str(c.get("date") or ""), time=str(c.get("time") or ""), duration_min=int(c.get("duration_min") or 60), location="", kind=str(c.get("kind") or "personal"), notes=str(c.get("notes") or ""))
        except Exception as e:
            created = {"ok": False, "error": f"{type(e).__name__}: {e}"}

    return {"ok": True, "mode": mode, "intent": it, "created": created}
