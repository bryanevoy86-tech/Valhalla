from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.go_live import GoLiveStateOut, GoLiveToggleIn, GoLiveChecklistOut
from app.services.go_live import read_state, checklist, set_go_live, set_kill_switch

router = APIRouter(prefix="/governance/go-live", tags=["Governance", "Go-Live"])


@router.get("/state", response_model=GoLiveStateOut)
def get_state(db: Session = Depends(get_db)) -> GoLiveStateOut:
    return read_state(db)


@router.get("/checklist", response_model=GoLiveChecklistOut)
def get_checklist(db: Session = Depends(get_db)) -> GoLiveChecklistOut:
    data = checklist(db)
    return GoLiveChecklistOut(**data)


@router.post("/enable", response_model=GoLiveStateOut)
def enable_go_live(body: GoLiveToggleIn, db: Session = Depends(get_db)) -> GoLiveStateOut:
    data = checklist(db)
    if not data["ok"]:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail={"message": "Go-live checklist failed", **data},
        )
    return set_go_live(db, True, body.changed_by, body.reason)


@router.post("/disable", response_model=GoLiveStateOut)
def disable_go_live(body: GoLiveToggleIn, db: Session = Depends(get_db)) -> GoLiveStateOut:
    return set_go_live(db, False, body.changed_by, body.reason)


@router.post("/kill-switch/engage", response_model=GoLiveStateOut)
def engage_kill_switch(body: GoLiveToggleIn, db: Session = Depends(get_db)) -> GoLiveStateOut:
    return set_kill_switch(db, True, body.changed_by, body.reason)


@router.post("/kill-switch/release", response_model=GoLiveStateOut)
def release_kill_switch(body: GoLiveToggleIn, db: Session = Depends(get_db)) -> GoLiveStateOut:
    return set_kill_switch(db, False, body.changed_by, body.reason)
