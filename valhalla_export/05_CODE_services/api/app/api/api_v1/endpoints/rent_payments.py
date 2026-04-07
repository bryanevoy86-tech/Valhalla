from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.rent_payment import RentPayment
from app.schemas.tenant_lease import (
    RentPaymentCreate,
    RentPaymentUpdate,
    RentPaymentOut,
)

router = APIRouter()


@router.post("/", response_model=RentPaymentOut)
def create_rent_payment(payload: RentPaymentCreate, db: Session = Depends(get_db)):
    obj = RentPayment(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=list[RentPaymentOut])
def list_rent_payments(
    lease_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(RentPayment)
    if lease_id is not None:
        query = query.filter(RentPayment.lease_id == lease_id)
    if status:
        query = query.filter(RentPayment.status == status)
    return query.all()


@router.put("/{payment_id}", response_model=RentPaymentOut)
def update_rent_payment(payment_id: int, payload: RentPaymentUpdate, db: Session = Depends(get_db)):
    obj = db.query(RentPayment).get(payment_id)
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
