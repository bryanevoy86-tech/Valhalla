"""PACK 89: Household OS Expansion
Household routines, chores, inventories, maintenance schedules.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean

from app.models.base import Base


class HouseholdTask(Base):
    __tablename__ = "household_task"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    assigned_to = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class HomeInventoryItem(Base):
    __tablename__ = "home_inventory"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    min_required = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
