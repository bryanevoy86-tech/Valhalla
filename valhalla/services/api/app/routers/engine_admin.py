from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.engines.states import EngineState
from app.services import engine_state as svc

router = APIRouter(prefix="/api/engines", tags=["Governance", "Engines"])


@router.get("/states")
def states(db: Session = Depends(get_db)):
    return {"engines": svc.list_states(db)}


@router.post("/transition")
def transition(payload: dict, db: Session = Depends(get_db)):
    engine_name = payload.get("engine_name")
    target_state = payload.get("target_state")
    changed_by = payload.get("changed_by", "system")
    reason = payload.get("reason")

    if not engine_name or not target_state:
        raise HTTPException(status_code=400, detail="engine_name and target_state required")

    try:
        target = EngineState(target_state)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid target_state: {target_state}")

    try:
        return svc.transition(db, engine_name, target, changed_by=changed_by, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
