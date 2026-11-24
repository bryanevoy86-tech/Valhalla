"""Durable internal closer session and operator notes."""

from sqlalchemy import JSON, Column, ForeignKey, Integer, String

from app.core.db import Base


class CloserSession(Base):
    __tablename__ = "closer_sessions"

    id = Column(String(36), primary_key=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    script = Column(JSON, nullable=False)
    last_section = Column(String(32), nullable=False)
    section_notes = Column(JSON, nullable=False, default=list)
    feedback = Column(JSON, nullable=True)
