from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.models.error_log import ErrorLog
from app.schemas.error_log import (
    ErrorLogCreate,
    ErrorLogUpdate,
    ErrorLogOut,
)

router = APIRouter()


@router.post("/", response_model=ErrorLogOut)
def create_error_log(
    payload: ErrorLogCreate,
    db: Session = Depends(get_db),
):
    obj = ErrorLog(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[ErrorLogOut])
def list_error_logs(
    source: str | None = None,
    severity: str | None = None,
    unresolved_only: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(ErrorLog)
    if source:
        query = query.filter(ErrorLog.source == source)
    if severity:
        query = query.filter(ErrorLog.severity == severity)
    if unresolved_only:
        query = query.filter(ErrorLog.resolved.is_(False))
    return query.order_by(ErrorLog.created_at.desc()).all()


@router.put("/{error_id}", response_model=ErrorLogOut)
def update_error_log(
    error_id: int,
    payload: ErrorLogUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(ErrorLog).get(error_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    if payload.resolved and not obj.resolved_at:
        obj.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj
