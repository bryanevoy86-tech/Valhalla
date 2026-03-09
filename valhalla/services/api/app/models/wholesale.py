"""
PACK X: Wholesaling Engine Models
Pipeline overlay for wholesale deals.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base


class WholesalePipeline(Base):
    __tablename__ = "wholesale_pipelines"

    id = Column(Integer, primary_key=True, index=True)

    # Link to your existing deal / property tables by ID
    deal_id = Column(Integer, nullable=True)
    property_id = Column(Integer, nullable=True)

    stage = Column(
        String,
        nullable=False,
        default="lead",  # lead, offer_made, under_contract, assigned, closed, dead
    )

    lead_source = Column(String, nullable=True)
    seller_motivation = Column(String, nullable=True)

    arv_estimate = Column(Float, nullable=True)          # After Repair Value
    max_allowable_offer = Column(Float, nullable=True)   # MAO
    assignment_fee_target = Column(Float, nullable=True)
    expected_spread = Column(Float, nullable=True)

    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    activities = relationship(
        "WholesaleActivityLog",
        back_populates="pipeline",
        cascade="all, delete-orphan",
    )


class WholesaleActivityLog(Base):
    __tablename__ = "wholesale_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, ForeignKey("wholesale_pipelines.id"), nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String, nullable=False)  # call, text, email, inspection, offer, note, etc.
    description = Column(String, nullable=True)

    created_by = Column(String, nullable=True)  # Heimdall, VA, user, etc.

    pipeline = relationship("WholesalePipeline", back_populates="activities")
