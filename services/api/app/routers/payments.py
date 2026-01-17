"""
Payments router.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.payments.schemas import PaymentCreate, PaymentOut
from app.payments.service import create_payment, get_payment_by_user

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=PaymentOut)
async def create_new_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    return create_payment(db=db, payment=payment)


@router.get("/user/{user_id}", response_model=List[PaymentOut])
async def get_user_payments(user_id: int, db: Session = Depends(get_db)):
    return get_payment_by_user(db=db, user_id=user_id)
