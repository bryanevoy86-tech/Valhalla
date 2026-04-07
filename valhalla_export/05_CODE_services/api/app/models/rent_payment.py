from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
import datetime
from app.db.base_class import Base


class RentPayment(Base):
    __tablename__ = "rent_payments"

    id = Column(Integer, primary_key=True, index=True)
    lease_id = Column(Integer, nullable=False)
    due_date = Column(DateTime, nullable=False)
    amount_due = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    paid_date = Column(DateTime)
    status = Column(String, default="pending")
    method = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
