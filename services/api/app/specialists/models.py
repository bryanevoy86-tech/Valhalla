from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.db import Base


class HumanSpecialist(Base):
    __tablename__ = "human_specialists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    name = Column(String(120), nullable=False)
    role = Column(String(60), nullable=False)  # lawyer | accountant | advisor
    email = Column(String(200), nullable=True)
    phone = Column(String(40), nullable=True)

    notes = Column(Text, nullable=True)
    expertise = Column(JSONB, nullable=True)


class SpecialistCaseComment(Base):
    __tablename__ = "specialist_case_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    specialist_id = Column(UUID(as_uuid=True), ForeignKey("human_specialists.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("god_review_cases.id", ondelete="CASCADE"), nullable=False)

    comment = Column(Text, nullable=True)
    payload = Column(JSONB, nullable=True)
