from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.db import Base


class GodCaseStatus(str):
    OPEN = "open"
    AWAITING_HUMAN = "awaiting_human"
    CLOSED = "closed"


class GodCaseOutcome(str):
    UNKNOWN = "unknown"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class GodReviewCase(Base):
    """
    A single decision thread that Heimdall, Loki, and a human expert
    all touch.

    Examples:
    - 'Buy this property under BRRRR in Florida?'
    - 'Adopt this new trust clause?'
    - 'Deploy this automation to all legacies?'
    """

    __tablename__ = "god_review_cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    subject_type = Column(
        String(100),
        nullable=False,
        doc="What this case is about (deal, contract, tax_plan, automation_change, etc.)",
    )
    subject_reference = Column(
        String(200),
        nullable=True,
        doc="ID or reference string Heimdall uses internally.",
    )

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    status = Column(
        String(30),
        nullable=False,
        default=lambda: GodCaseStatus.OPEN,
    )

    heimdall_summary = Column(Text, nullable=True)
    loki_summary = Column(Text, nullable=True)
    human_summary = Column(Text, nullable=True)

    heimdall_payload = Column(JSONB, nullable=True)
    loki_payload = Column(JSONB, nullable=True)
    human_payload = Column(JSONB, nullable=True)

    final_outcome = Column(
        String(30),
        nullable=False,
        default=lambda: GodCaseOutcome.UNKNOWN,
    )

    final_notes = Column(Text, nullable=True)

    events = relationship(
        "GodReviewEvent",
        back_populates="case",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class GodReviewEvent(Base):
    """
    Timeline of what happened inside a GodReviewCase.
    Heimdall suggestion, Loki critique, human edits, final sign-off, etc.
    """

    __tablename__ = "god_review_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    case_id = Column(
        UUID(as_uuid=True),
        ForeignKey("god_review_cases.id", ondelete="CASCADE"),
        nullable=False,
    )

    actor = Column(
        String(30),
        nullable=False,
        doc="heimdall | loki | human | system",
    )
    event_type = Column(
        String(50),
        nullable=False,
        doc="suggestion | review | override | comment | decision | sync",
    )

    message = Column(Text, nullable=True)
    payload = Column(JSONB, nullable=True)

    case = relationship("GodReviewCase", back_populates="events")
