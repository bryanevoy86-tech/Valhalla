from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.system_health import SystemHealthSnapshot
from app.schemas.system_health import (
    SystemHealthSnapshotCreate,
    SystemHealthSnapshotOut,
)

router = APIRouter()


@router.post("/", response_model=SystemHealthSnapshotOut)
def create_system_health_snapshot(
    payload: SystemHealthSnapshotCreate,
    db: Session = Depends(get_db),
):
    obj = SystemHealthSnapshot(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[SystemHealthSnapshotOut])
def list_system_health_snapshots(
    scope: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(SystemHealthSnapshot)
    if scope:
        query = query.filter(SystemHealthSnapshot.scope == scope)
    return query.order_by(SystemHealthSnapshot.created_at.desc()).all()
