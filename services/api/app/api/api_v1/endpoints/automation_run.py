from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.automation_run import AutomationRun
from app.schemas.automation_run import (
    AutomationRunCreate,
    AutomationRunUpdate,
    AutomationRunOut,
)

router = APIRouter()


@router.post("/", response_model=AutomationRunOut)
def create_automation_run(
    payload: AutomationRunCreate,
    db: Session = Depends(get_db),
):
    obj = AutomationRun(
        rule_id=payload.rule_id,
        rule_name=payload.rule_name,
        status=payload.status,
        severity=payload.severity,
        input_snapshot=payload.input_snapshot,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[AutomationRunOut])
def list_automation_runs(
    rule_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(AutomationRun)
    if rule_id is not None:
        query = query.filter(AutomationRun.rule_id == rule_id)
    if status is not None:
        query = query.filter(AutomationRun.status == status)
    return query.order_by(AutomationRun.created_at.desc()).all()


@router.put("/{run_id}", response_model=AutomationRunOut)
def update_automation_run(
    run_id: int,
    payload: AutomationRunUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(AutomationRun).get(run_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    if payload.status in ("success", "failed", "skipped") and not obj.finished_at:
        obj.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj
