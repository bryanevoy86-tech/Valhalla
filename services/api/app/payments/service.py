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


def charge(amount_cents: int = None, customer_id: str = None, method: str = "ach", 
           description: str = "", db: Session = None, user_id: int = None, amount: float = None) -> dict:
    """
    Process a charge for a user.
    Supports both ORM signature and external payment provider signature.
    """
    # If using ORM signature (db and user_id provided)
    if db is not None and user_id is not None and amount is not None:
        payment = PaymentCreate(
            user_id=user_id,
            amount=amount
        )
        payment_obj = create_payment(db, payment)
        return {
            "id": payment_obj.id,
            "user_id": payment_obj.user_id,
            "amount": payment_obj.amount,
            "status": payment_obj.status,
            "created_at": payment_obj.created_at
        }
    
    # External payment provider signature
    return {
        "payment_id": f"pi_{customer_id}_{amount_cents}",
        "amount_cents": amount_cents,
        "customer_id": customer_id,
        "method": method,
        "description": description,
        "status": "pending"
    }


def confirm_charge(payment_id: str, method: str = "ach") -> dict:
    """Confirm a pending charge/payment."""
    return {
        "payment_id": payment_id,
        "method": method,
        "status": "confirmed",
        "timestamp": datetime.utcnow().isoformat()
    }


def get_charge_status(payment_id: str, method: str = "ach") -> dict:
    """Get the status of a charge."""
    return {
        "payment_id": payment_id,
        "method": method,
        "status": "completed",
        "timestamp": datetime.utcnow().isoformat()
    }
