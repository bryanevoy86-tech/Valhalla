from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class AIPersona(Base):
    __tablename__ = "ai_personas"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False, unique=True)      # "Heimdall", "Loki", etc.
    code = Column(String, nullable=False, unique=True)      # "HEIMDALL_CORE", "LOKI_AUDIT"
    role = Column(String, nullable=False)                   # "guardian", "countermind", "closer", etc.
    description = Column(Text)

    primary_domains = Column(String)                        # comma list: "real_estate,tax,arbitrage"
    active = Column(Boolean, default=True)

    # simple persona style flags
    tone = Column(String, default="neutral")                # "calm", "aggressive", etc.
    safety_level = Column(String, default="high")           # high/medium/low (internal logic only)

    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
