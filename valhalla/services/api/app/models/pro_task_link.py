# services/api/app/models/pro_task_link.py

from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class ProfessionalTaskLink(Base):
    """
    Links tasks to professionals for tracking what's waiting on which human.
    Lightweight linking table between deals, professionals, and tasks.
    """

    __tablename__ = "professional_task_links"

    id = Column(Integer, primary_key=True, index=True)

    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    deal_id = Column(Integer, nullable=False)  # can be FK to deals table later
    task_id = Column(Integer, nullable=False)  # can be FK to tasks table later

    status = Column(String(50), default="open")  # open, in_progress, blocked, done
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    professional = relationship("Professional", back_populates="task_links")
