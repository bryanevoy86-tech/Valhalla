from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.integrity_event import IntegrityEvent
from app.schemas.integrity import IntegrityEventCreate, IntegrityEventOut

router = APIRouter()


@router.post("/", response_model=IntegrityEventOut)
def create_integrity_event(payload: IntegrityEventCreate, db: Session = Depends(get_db)):
    obj = IntegrityEvent(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[IntegrityEventOut])
def list_integrity_events(
    category: str | None = None,
    severity: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(IntegrityEvent)
    if category:
        query = query.filter(IntegrityEvent.category == category)
    if severity:
        query = query.filter(IntegrityEvent.severity == severity)
    if entity_type:
        query = query.filter(IntegrityEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(IntegrityEvent.entity_id == entity_id)
    return query.all()
