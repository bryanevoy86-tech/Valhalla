from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.resort_booking import ResortBooking
from app.schemas.resort import ResortBookingCreate, ResortBookingUpdate, ResortBookingOut

router = APIRouter()

@router.post("/", response_model=ResortBookingOut)
def new_booking(payload: ResortBookingCreate, db: Session = Depends(get_db)):
    # dynamic pricing will get added in Pack 76
    obj = ResortBooking(**payload.dict(), dynamic_price=payload.base_price)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/", response_model=list[ResortBookingOut])
def list_bookings(db: Session = Depends(get_db)):
    return db.query(ResortBooking).all()

@router.put("/{booking_id}", response_model=ResortBookingOut)
def update_booking(booking_id: int, payload: ResortBookingUpdate, db: Session = Depends(get_db)):
    obj = db.query(ResortBooking).get(booking_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
