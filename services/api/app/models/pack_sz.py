"""
PACK SZ: Core Philosophy & "Why I Built Valhalla" Archive

Models for capturing your core philosophy, values, principles, and rules.
This is the soul of Valhalla — structured, factual, unchanging guidance.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base


class PhilosophyRecord(Base):
    """
    Records your core philosophy: why Valhalla exists, what you stand for, and what you protect.
    """
    __tablename__ = "philosophy_record"

    id = Column(Integer, primary_key=True)
    record_id = Column(String(32), unique=True, nullable=False)  # Prefix: phil
    title = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    pillars = Column(JSON, nullable=False, default=[])  # Core beliefs
    mission_statement = Column(Text, nullable=False)
    values = Column(JSON, nullable=False, default=[])  # User-defined values
    rules_to_follow = Column(JSON, nullable=False, default=[])  # Guiding rules
    rules_to_never_break = Column(JSON, nullable=False, default=[])  # Non-negotiables
    long_term_intent = Column(Text, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    principles = relationship("EmpirePrinciple", back_populates="record", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PhilosophyRecord {self.record_id}: {self.title}>"


class EmpirePrinciple(Base):
    """
    Individual principle that guides Valhalla's operation and decisions.
    """
    __tablename__ = "empire_principle"

    id = Column(Integer, primary_key=True)
    principle_id = Column(String(32), unique=True, nullable=False)  # Prefix: prin
    record_id = Column(Integer, ForeignKey("philosophy_record.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(32), nullable=False)  # ethics, growth, family, wealth, behavior, decision_making
    description = Column(Text, nullable=False)
    enforcement_level = Column(String(16), nullable=False, default="soft")  # soft, strong
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    record = relationship("PhilosophyRecord", back_populates="principles")

    def __repr__(self):
        return f"<EmpirePrinciple {self.principle_id}: {self.category}>"


class PhilosophySnapshot(Base):
    """
    Periodic snapshot of philosophy, principles, and how they impact the system.
    """
    __tablename__ = "philosophy_snapshot"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(32), unique=True, nullable=False)  # Prefix: philsnap
    date = Column(Date, nullable=False)
    core_pillars = Column(JSON, nullable=False, default=[])  # Current core beliefs
    recent_updates = Column(JSON, nullable=False, default=[])  # What changed
    impact_on_system = Column(JSON, nullable=False, default=[])  # System implications
    user_notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<PhilosophySnapshot {self.snapshot_id}: {self.date}>"
