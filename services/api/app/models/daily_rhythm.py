"""
PACK TO: Daily Rhythm & Tempo Models
Stores your ideal daily structure and Heimdall tempo rules.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, JSON
from app.models.base import Base


class DailyRhythmProfile(Base):
    __tablename__ = "daily_rhythm_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="default")
    wake_time = Column(String, nullable=True)          # "07:00"
    sleep_time = Column(String, nullable=True)         # "23:00"
    peak_focus_blocks = Column(JSON, nullable=True)    # list[{start, end}]
    low_energy_blocks = Column(JSON, nullable=True)    # list[{start, end}]
    family_blocks = Column(JSON, nullable=True)        # list[{start, end}]
    personal_time_blocks = Column(JSON, nullable=True) # list[{start, end}]
    notes = Column(Text, nullable=True)
    active = Column(Boolean, default=True)


class TempoRule(Base):
    __tablename__ = "tempo_rules"

    id = Column(Integer, primary_key=True, index=True)
    profile_name = Column(String, nullable=False, default="default")
    time_block = Column(String, nullable=False)        # morning, afternoon, evening, night
    action_intensity = Column(String, nullable=False)  # push, balanced, gentle
    communication_style = Column(String, nullable=False)  # short, detailed, none, check_in
    notes = Column(Text, nullable=True)
