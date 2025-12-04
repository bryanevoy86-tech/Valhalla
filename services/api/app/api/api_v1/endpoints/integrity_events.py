from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.integrity_event import IntegrityEvent
from app.schemas.integrity_event import (
    IntegrityEventCreate,
    IntegrityEventUpdate,
    IntegrityEventOut,
)

router = APIRouter()


@router.post("/", response_model=IntegrityEventOut)
def create_integrity_event(
    payload: IntegrityEventCreate,
    db: Session = Depends(get_db),
):
    obj = IntegrityEvent(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[IntegrityEventOut])
def list_integrity_events(
    severity: str | None = None,
    requires_human_review: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(IntegrityEvent)
    if severity:
        query = query.filter(IntegrityEvent.severity == severity)
    if requires_human_review is not None:
        query = query.filter(
            IntegrityEvent.requires_human_review == requires_human_review
        )
    return query.order_by(IntegrityEvent.created_at.desc()).all()


@router.put("/{event_id}", response_model=IntegrityEventOut)
def update_integrity_event(
    event_id: int,
    payload: IntegrityEventUpdate,
    db: Session = Depends(get_db),
):
    obj = db.query(IntegrityEvent).get(event_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
