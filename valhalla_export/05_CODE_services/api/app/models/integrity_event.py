from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from app.db.base_class import Base
import datetime


class IntegrityEvent(Base):
    __tablename__ = "integrity_events"

    id = Column(Integer, primary_key=True, index=True)

    event_type = Column(String, nullable=False)        # "TRANSFER", "CLONE_LAUNCH", etc.
    severity = Column(String, default="info")          # info/warn/critical

    # who triggered
    actor_type = Column(String, nullable=False)        # "user", "ai", "system"
    actor_name = Column(String, nullable=False)        # "Bryan", "Heimdall", "Loki"

    legacy_code = Column(String)
    vault_name = Column(String)
    amount = Column(Float, default=0.0)
    currency = Column(String, default="CAD")

    description = Column(Text)
    metadata_json = Column(Text)                       # free-form JSON string

    requires_human_review = Column(Boolean, default=False)
    reviewed = Column(Boolean, default=False)
    review_note = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


__all__ = ["IntegrityEvent"]
