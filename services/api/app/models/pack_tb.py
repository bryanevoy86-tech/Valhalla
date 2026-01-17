"""
PACK TB: Daily Behavioral Rhythm & Tempo Engine

Models for capturing your ideal daily structure, energy blocks, and how Heimdall should operate.
No emotion analysis — purely scheduling and behavioral pacing.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class DailyRhythmProfile(Base):
    """
    Your ideal daily structure: when you work best, when you need quiet, energy blocks, etc.
    This is how Heimdall knows when to push and when to back off.
    """
    __tablename__ = "daily_rhythm_profile"

    id = Column(Integer, primary_key=True)
    profile_id = Column(String(32), unique=True, nullable=False)  # Prefix: rhythm
    wake_time = Column(String(5), nullable=False)  # HH:MM format
    sleep_time = Column(String(5), nullable=False)  # HH:MM format
    peak_focus_blocks = Column(JSON, nullable=False, default=[])  # [{start: HH:MM, end: HH:MM}, ...]
    low_energy_blocks = Column(JSON, nullable=False, default=[])  # [{start: HH:MM, end: HH:MM}, ...]
    family_blocks = Column(JSON, nullable=False, default=[])  # [{start: HH:MM, end: HH:MM}, ...]
    personal_time_blocks = Column(JSON, nullable=False, default=[])  # [{start: HH:MM, end: HH:MM}, ...]
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    tempo_rules = relationship("TempoRule", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DailyRhythmProfile {self.profile_id}>"


class TempoRule(Base):
    """
    Rules for how Heimdall should behave during specific time blocks.
    Controls intensity, communication style, and pacing.
    """
    __tablename__ = "tempo_rule"

    id = Column(Integer, primary_key=True)
    rule_id = Column(String(32), unique=True, nullable=False)  # Prefix: tempo
    profile_id = Column(Integer, ForeignKey("daily_rhythm_profile.id", ondelete="CASCADE"), nullable=False)
    time_block = Column(String(32), nullable=False)  # morning, afternoon, evening, night
    action_intensity = Column(String(16), nullable=False)  # push, balanced, gentle
    communication_style = Column(String(32), nullable=False)  # short, detailed, none, check_in
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    profile = relationship("DailyRhythmProfile", back_populates="tempo_rules")

    def __repr__(self):
        return f"<TempoRule {self.rule_id}: {self.time_block}>"


class DailyTempoSnapshot(Base):
    """
    Daily snapshot tracking whether rhythm was followed and any adjustments needed.
    """
    __tablename__ = "daily_tempo_snapshot"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(String(32), unique=True, nullable=False)  # Prefix: daytemp
    date = Column(Date, nullable=False)
    rhythm_followed = Column(Boolean, nullable=False, default=True)
    adjustments_needed = Column(Text)
    user_notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<DailyTempoSnapshot {self.snapshot_id}: {self.date}>"
