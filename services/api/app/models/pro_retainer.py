# services/api/app/models/pro_retainer.py

from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Float,
    ForeignKey,
    Boolean,
    func,
    DateTime,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class Retainer(Base):
    """
    Retainer agreement with a professional (lawyer, accountant, consultant).
    Tracks hours, costs, renewal dates, and consumption.
    """

    __tablename__ = "retainers"

    id = Column(Integer, primary_key=True, index=True)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)

    name = Column(String(200), nullable=False)
    monthly_hours_included = Column(Float, nullable=False)
    hourly_rate = Column(Float, nullable=True)
    renewal_date = Column(Date, nullable=False)

    hours_used = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    professional = relationship("Professional", back_populates="retainers")
