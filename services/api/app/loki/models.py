"""Loki AI review models for risk, compliance, and artifact analysis."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    JSON,
    Uuid,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")
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

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    artifact_sha256 = Column(String(64), unique=True, nullable=True)
    heimdall_reference_id = Column(String(100), nullable=True)
    human_reference_id = Column(String(100), nullable=True)

    summary = Column(Text, nullable=True)
    result_severity = Column(String(20), nullable=True)

    raw_input = Column(JSON_TYPE, nullable=False)
    raw_output = Column(JSON_TYPE, nullable=True)

    findings = relationship(
        "LokiFinding",
        back_populates="review",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class LokiFinding(Base):
    """Individual finding within a Loki review."""
    __tablename__ = "loki_findings"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    review_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("loki_reviews.id", ondelete="CASCADE"),
        nullable=False,
    )

    category = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    suggested_fix = Column(Text, nullable=True)
    tags = Column(JSON_TYPE, nullable=True)

    review = relationship("LokiReview", back_populates="findings")


class LokiIndependentReceipt(Base):
    """Receipt written exclusively by the independent reviewer interface."""

    __tablename__ = "loki_independent_receipts"

    review_id = Column(Uuid(as_uuid=True), ForeignKey("loki_reviews.id", ondelete="CASCADE"), primary_key=True)
    artifact_sha256 = Column(String(64), nullable=False)
    reviewer_id = Column(String(100), nullable=False)
    analysis_ref = Column(String(200), nullable=False)
    result_sha256 = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


class LokiReconsideration(Base):
    """Owner decision on exactly one reviewed version and its material findings."""

    __tablename__ = "loki_reconsiderations"

    review_id = Column(Uuid(as_uuid=True), ForeignKey("loki_independent_receipts.review_id", ondelete="CASCADE"), primary_key=True)
    artifact_sha256 = Column(String(64), nullable=False)
    disposition = Column(String(24), nullable=False)
    material_finding_ids = Column(JSON_TYPE, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
