from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Float,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.sql import func

from .base import Base  # <- whatever your Base class file is called


class LegacyStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    SCALING = "SCALING"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class LegacySystem(Base):
    __tablename__ = "legacy_systems"

    id = Column(Integer, primary_key=True, index=True)

    # Human-readable label for this legacy instance
    code_name = Column(String(100), nullable=False, index=True)

    # Which template / pattern it comes from, e.g. "VALHALLA_V1"
    template_key = Column(String(100), nullable=False, index=True)

    # Status in the lifecycle (see LegacyStatus enum)
    status = Column(
        SAEnum(LegacyStatus, name="legacy_status_enum"),
        nullable=False,
        default=LegacyStatus.NOT_STARTED,
        index=True,
    )

    # Optional reference to another legacy this was cloned from
    cloned_from = Column(String(100), nullable=True)

    # Is this one of the 5 original legacies?
    is_primary = Column(Boolean, nullable=False, default=False)

    # How "healthy" the legacy is (0–100)
    health_score = Column(Float, nullable=False, default=100.0)

    # How many times this legacy has spawned new copies / mirrors
    clone_count = Column(Integer, nullable=False, default=0)

    # Last time a clone/mirror was spawned from this legacy
    last_clone_at = Column(DateTime(timezone=True), nullable=True)

    # Freeform notes Heimdall can use for reasoning
    notes = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
