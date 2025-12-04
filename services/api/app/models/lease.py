from sqlalchemy import Column, Integer, String, Float, DateTime
import datetime
from app.db.base_class import Base


class Lease(Base):
    __tablename__ = "leases"

    id = Column(Integer, primary_key=True, index=True)
    rental_property_id = Column(Integer, nullable=False)
    tenant_id = Column(Integer, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    rent_amount = Column(Float, nullable=False)
    rent_currency = Column(String, default="CAD")
    frequency = Column(String, default="monthly")
    deposit_amount = Column(Float, default=0.0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
