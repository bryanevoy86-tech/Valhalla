from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, Boolean

from app.db.base import Base


class HeimdallBuyer(Base):
    __tablename__ = "heimdall_buyers"

    id = Column(String, primary_key=True, index=True)
    buyer_name = Column(String, nullable=False, index=True)
    company_name = Column(String, nullable=True)
    email = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True)
    target_markets = Column(JSON, default=list)
    property_types = Column(JSON, default=list)
    buy_box = Column(JSON, default=dict)
    proof_of_funds_verified = Column(Boolean, default=False)
    buyer_status = Column(String, default="ACTIVE", index=True)
    reliability_score = Column(String, default="unknown")
    close_speed = Column(String, default="unknown")
    notes = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
