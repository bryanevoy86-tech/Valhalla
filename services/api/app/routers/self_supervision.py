"""
PACK CL13: Self-Supervision Router
Prefix: /heimdall/supervision
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.self_supervision import (
    SelfSupervisionRunCreate,
    SelfSupervisionRunOut,
    SelfSupervisionRunList,
    SelfSupervisionFindingList,
    SelfSupervisionFindingOut,
)
from app.services.self_supervision import create_run, list_runs, list_findings

router = APIRouter(prefix="/heimdall/supervision", tags=["Heimdall", "Meta-Learning"])


@router.post("/runs", response_model=SelfSupervisionRunOut, status_code=201)
def create_supervision_run(payload: SelfSupervisionRunCreate, db: Session = Depends(get_db)):
    return create_run(db, payload)


@router.get("/runs", response_model=SelfSupervisionRunList)
def get_supervision_runs(
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    items = list_runs(db, limit=limit)
    return SelfSupervisionRunList(total=len(items), items=[SelfSupervisionRunOut.model_validate(i) for i in items])


@router.get("/findings", response_model=SelfSupervisionFindingList)
def get_supervision_findings(
    run_id: Optional[str] = Query(None),
    unresolved_only: bool = Query(False),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    items = list_findings(db, run_id=run_id, unresolved_only=unresolved_only, limit=limit)
    return SelfSupervisionFindingList(total=len(items), items=[SelfSupervisionFindingOut.model_validate(i) for i in items])
