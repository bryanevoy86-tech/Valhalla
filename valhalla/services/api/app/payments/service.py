"""
Payment service logic.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.payments.models import Payment
from app.payments.schemas import PaymentCreate


def create_payment(db: Session, payment: PaymentCreate) -> Payment:
    db_payment = Payment(
        user_id=payment.user_id,
        amount=payment.amount,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment


def get_payment_by_user(db: Session, user_id: int) -> list[Payment]:
    return db.query(Payment).filter(Payment.user_id == user_id).all()
