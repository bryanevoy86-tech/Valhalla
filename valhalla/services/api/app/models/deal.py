"""Backend Deal model for services/api (copied from backend for orchestration)."""

from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.db import Base


class Deal(Base):
    __tablename__ = "deals"
    __table_args__ = {'extend_existing': True}  # Allow re-definition if table exists
    
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    legacy_id = Column(
        Integer, ForeignKey("legacies.id", ondelete="SET NULL"), index=True, nullable=True
    )
    status = Column(String, nullable=False, default="draft")
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    created_at = Column(String, nullable=True)
    # legacy fields for backward compatibility
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)
    arv = Column(Float, default=0.0)
    repairs = Column(Float, default=0.0)
    offer = Column(Float, default=0.0)
    mao = Column(Float, default=0.0)
    roi_note = Column(String, default="")
