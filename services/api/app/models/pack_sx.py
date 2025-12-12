"""
PACK SX: Emotional Neutrality & Stability Log (Safe, Non-Psych, User Input Only)

Models for tracking user-stated emotional and logistical states without interpretation or diagnosis.
Heimdall uses this to understand context and adjust operational cadence.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, JSON, Float
from sqlalchemy.sql import func
from app.models.base import Base


class EmotionalStateEntry(Base):
    """
    User-stated emotional and cognitive state without interpretation or diagnosis.
    """
    __tablename__ = "emotional_state_entry"

    id = Column(Integer, primary_key=True)
    entry_id = Column(String(32), unique=True, nullable=False)  # Prefix: emote
    date = Column(Date, nullable=False)
    self_reported_mood = Column(String(255), nullable=False)  # User's own words: "tired", "angry", etc.
    energy_level = Column(Integer, nullable=False)  # 1-10 user-defined
    cognitive_load = Column(Integer, nullable=False)  # 1-10 user-defined
    context = Column(Text, nullable=False)  # What's happening (factual)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<EmotionalStateEntry {self.entry_id}: {self.date}>"


class StabilityLog(Base):
    """
    Non-analytical log of daily events, stress factors, and relief actions.
    Compiled from user input without interpretation.
    """
    __tablename__ = "stability_log"

    id = Column(Integer, primary_key=True)
    log_id = Column(String(32), unique=True, nullable=False)  # Prefix: stablog
    date = Column(Date, nullable=False)
    events_today = Column(JSON, nullable=False, default=[])  # List of events (user-entered)
    stress_factors = Column(JSON, nullable=False, default=[])  # List of stress factors (user-entered)
    relief_actions = Column(JSON, nullable=False, default=[])  # List of relief actions (user-entered)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<StabilityLog {self.log_id}: {self.date}>"


class NeutralSummary(Base):
    """
    Weekly compilation of emotional/logistical states with no analysis or interpretation.
    Heimdall compiles; you interpret.
    """
    __tablename__ = "neutral_summary"

    id = Column(Integer, primary_key=True)
    summary_id = Column(String(32), unique=True, nullable=False)  # Prefix: neusumm
    week_of = Column(String(10), nullable=False)  # YYYY-WXX format
    average_energy = Column(Float, nullable=False, default=0.0)  # Average of energy_level entries
    task_load = Column(Float, nullable=False, default=0.0)  # Aggregated task/load indicator
    user_highlights = Column(JSON, nullable=False, default=[])  # What user identified as positive
    user_defined_interpretation = Column(Text)  # User's own interpretation (not Heimdall's)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<NeutralSummary {self.summary_id}: {self.week_of}>"
