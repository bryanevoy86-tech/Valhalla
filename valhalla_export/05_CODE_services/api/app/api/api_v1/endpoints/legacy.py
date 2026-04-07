from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.legacy import Legacy
from app.schemas.legacy import LegacyCreate, LegacyUpdate, LegacyOut
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=LegacyOut)
def create_legacy(payload: LegacyCreate, db: Session = Depends(get_db)):
    obj = Legacy(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[LegacyOut])
def list_legacies(db: Session = Depends(get_db)):
    return db.query(Legacy).all()

@router.put("/{legacy_id}", response_model=LegacyOut)
def update_legacy(legacy_id: int, payload: LegacyUpdate, db: Session = Depends(get_db)):
    obj = db.query(Legacy).get(legacy_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.post("/{legacy_id}/clone", response_model=LegacyOut)
def clone_legacy(legacy_id: int, db: Session = Depends(get_db)):
    obj = db.query(Legacy).get(legacy_id)
    obj.status = "cloned"
    obj.last_clone_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return obj
