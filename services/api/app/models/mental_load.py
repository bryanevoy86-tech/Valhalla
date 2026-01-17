"""
PACK SN: Mental Load Offloading Engine
Models for brain externalization, task tracking, and daily load management
"""
from sqlalchemy import String, Integer, Text, DateTime, Boolean, JSON, Column
from sqlalchemy.sql import func
from app.models.base import Base


class MentalLoadEntry(Base):
    """User-defined mental load item with urgency and emotional weight."""
    __tablename__ = 'mental_load_entries'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=False)  # task, worry, reminder, idea, future, household
    description = Column(Text, nullable=False)
    urgency_level = Column(Integer, nullable=True)  # 1-5, user-defined
    emotional_weight = Column(Integer, nullable=True)  # 1-10, user-defined (NOT interpreted)
    action_required = Column(Boolean, nullable=False, server_default="0")
    cleared = Column(Boolean, nullable=False, server_default="0")
    cleared_date = Column(DateTime, nullable=True)
    user_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())


class DailyLoadSummary(Base):
    """Daily aggregation of mental load items with action summary."""
    __tablename__ = 'daily_load_summaries'
    
    id = Column(Integer, primary_key=True)
    summary_id = Column(String(255), nullable=False, unique=True)
    date = Column(DateTime, nullable=False)
    total_items = Column(Integer, nullable=False)
    urgent_items = Column(JSON, nullable=True)  # [string]: high urgency items
    action_items = Column(JSON, nullable=True)  # [string]: items requiring action today
    delegated_items = Column(JSON, nullable=True)  # [string]: items delegated to others
    cleared_items = Column(JSON, nullable=True)  # [string]: items cleared/completed today
    waiting_items = Column(JSON, nullable=True)  # [string]: items awaiting response
    parked_items = Column(JSON, nullable=True)  # [string]: items deferred to later
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class LoadOffloadWorkflow(Base):
    """Brain dump and workflow state for rapid entry processing."""
    __tablename__ = 'load_offload_workflows'
    
    id = Column(Integer, primary_key=True)
    workflow_id = Column(String(255), nullable=False, unique=True)
    brain_dump = Column(Text, nullable=True)  # Raw user input
    processed_count = Column(Integer, nullable=False, server_default="0")
    categorized_items = Column(JSON, nullable=True)  # [{entry_id, category, urgency}]
    workflow_stage = Column(String(50), nullable=False, server_default="intake")  # intake, categorizing, ready
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
