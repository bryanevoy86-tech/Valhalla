from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.rental_property import RentalProperty
from app.schemas.rental_property import (
    RentalPropertyCreate,
    RentalPropertyUpdate,
    RentalPropertyOut,
)

router = APIRouter()


@router.post("/", response_model=RentalPropertyOut)
def create_rental_property(payload: RentalPropertyCreate, db: Session = Depends(get_db)):
    obj = RentalProperty(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[RentalPropertyOut])
def list_rental_properties(
    legacy_code: str | None = None,
    zone_code: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(RentalProperty)
    if legacy_code:
        query = query.filter(RentalProperty.legacy_code == legacy_code)
    if zone_code:
        query = query.filter(RentalProperty.zone_code == zone_code)
    if status:
        query = query.filter(RentalProperty.status == status)
    return query.all()


@router.put("/{property_id}", response_model=RentalPropertyOut)
def update_rental_property(property_id: int, payload: RentalPropertyUpdate, db: Session = Depends(get_db)):
    obj = db.query(RentalProperty).get(property_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
