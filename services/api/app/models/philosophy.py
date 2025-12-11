"""
PACK TM: Core Philosophy Archive Models
Stores your core pillars, values, and non-negotiable rules.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.models.base import Base


class PhilosophyRecord(Base):
    __tablename__ = "philosophy_records"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)              # e.g. "Why I Built Valhalla"
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    pillars = Column(Text, nullable=True)               # newline-separated
    mission_statement = Column(Text, nullable=True)
    values = Column(Text, nullable=True)                # newline-separated
    rules_to_follow = Column(Text, nullable=True)       # newline-separated
    rules_to_never_break = Column(Text, nullable=True)  # newline-separated
    long_term_intent = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


class EmpirePrinciple(Base):
    __tablename__ = "empire_principles"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)           # ethics, growth, family, etc.
    description = Column(Text, nullable=False)
    enforcement_level = Column(String, nullable=False, default="soft")  # soft, strong
    notes = Column(Text, nullable=True)
