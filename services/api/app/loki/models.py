"""Loki AI review models for risk, compliance, and artifact analysis."""
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


class LokiReviewStatus(str):
    """Enum-like class for Loki review status values."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class LokiResultSeverity(str):
    """Enum-like class for result severity levels."""
    OK = "ok"
    WARN = "warn"
    CRITICAL = "critical"


class LokiReview(Base):
    """Main review record for Loki AI artifact analysis."""
    __tablename__ = "loki_reviews"

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

    input_source = Column(String(100), nullable=False)
    artifact_type = Column(String(100), nullable=False)
    risk_profile = Column(String(100), nullable=True)

    status = Column(
        String(20),
        nullable=False,
        default=LokiReviewStatus.QUEUED,
    )

    heimdall_reference_id = Column(String(100), nullable=True)
    human_reference_id = Column(String(100), nullable=True)

    summary = Column(Text, nullable=True)
    result_severity = Column(String(20), nullable=True)

    raw_input = Column(JSONB, nullable=False)
    raw_output = Column(JSONB, nullable=True)

    findings = relationship(
        "LokiFinding",
        back_populates="review",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LokiFinding(Base):
    """Individual finding within a Loki review."""
    __tablename__ = "loki_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    review_id = Column(
        UUID(as_uuid=True),
        ForeignKey("loki_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )

    category = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)

    review = relationship("LokiReview", back_populates="findings")
