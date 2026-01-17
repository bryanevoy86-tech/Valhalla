from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from app.db.base_class import Base
import datetime

class QueenStream(Base):
    __tablename__ = "queen_streams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String)
    status = Column(String, default="active")
    monthly_target = Column(Float, default=0.0)
    current_estimate = Column(Float, default=0.0)
    auto_tax_handled = Column(Boolean, default=True)
    auto_vault_allocation = Column(Boolean, default=True)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
