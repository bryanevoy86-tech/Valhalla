from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.empire_snapshot import EmpireSnapshot
from app.schemas.snapshot import EmpireSnapshotCreate, EmpireSnapshotOut

router = APIRouter()


@router.post("/", response_model=EmpireSnapshotOut)
def create_snapshot(payload: EmpireSnapshotCreate, db: Session = Depends(get_db)):
    obj = EmpireSnapshot(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[EmpireSnapshotOut])
def list_snapshots(snapshot_type: str | None = None, db: Session = Depends(get_db)):
    query = db.query(EmpireSnapshot)
    if snapshot_type:
        query = query.filter(EmpireSnapshot.snapshot_type == snapshot_type)
    return query.all()


@router.get("/{snapshot_id}", response_model=EmpireSnapshotOut)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    obj = db.query(EmpireSnapshot).get(snapshot_id)
    return obj
