from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.shield_event import ShieldEvent
from app.schemas.shield import ShieldEventCreate, ShieldEventUpdate, ShieldEventOut

router = APIRouter()

@router.post("/", response_model=ShieldEventOut)
def new_event(payload: ShieldEventCreate, db: Session = Depends(get_db)):
    obj = ShieldEvent(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[ShieldEventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(ShieldEvent).all()

@router.put("/{event_id}", response_model=ShieldEventOut)
def update_event(event_id: int, payload: ShieldEventUpdate, db: Session = Depends(get_db)):
    obj = db.query(ShieldEvent).get(event_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
