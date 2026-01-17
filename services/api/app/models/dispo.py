"""
PACK Y: Disposition Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class DispoBuyerProfile(Base):
    __tablename__ = "dispo_buyer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    buy_box_summary = Column(String, nullable=True)  # zip/area, beds/baths, price range, etc.
    notes = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignments = relationship("DispoAssignment", back_populates="buyer")


class DispoAssignment(Base):
    __tablename__ = "dispo_assignments"

    id = Column(Integer, primary_key=True, index=True)

    pipeline_id = Column(Integer, nullable=False)  # from WholesalePipeline.id
    buyer_id = Column(Integer, ForeignKey("dispo_buyer_profiles.id"), nullable=False)

    status = Column(
        String,
        nullable=False,
        default="offered",  # offered, assigned, closed, fallout
    )

    assignment_price = Column(Float, nullable=True)
    assignment_fee = Column(Float, nullable=True)

    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer = relationship("DispoBuyerProfile", back_populates="assignments")
