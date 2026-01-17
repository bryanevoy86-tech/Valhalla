"""
PACK TK: Life Timeline & Milestones Models
Tracks major life events and milestones.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.db import Base


class LifeEvent(Base):
    __tablename__ = "life_events"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    title = Column(String, nullable=False)
    category = Column(String, nullable=True)  # personal, family, business, financial, health, achievement
    description = Column(Text, nullable=True)
    impact_level = Column(Integer, nullable=True)  # 1–5 user-defined
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<LifeEvent(title={self.title}, date={self.date})>"


class LifeMilestone(Base):
    __tablename__ = "life_milestones"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, nullable=True)  # can be linked to LifeEvent or standalone
    milestone_type = Column(String, nullable=False)  # start, finish, transition, achievement
    description = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<LifeMilestone(type={self.milestone_type}, description={self.description[:30]}...)>"
