"""
PACK TE: Life Roles & Capacity Models
Tracks your roles and how much capacity you have in each.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float

from app.core.db import Base


class LifeRole(Base):
    __tablename__ = "life_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # dad, builder, partner, operator, etc.
    domain = Column(String, nullable=True)  # family, business, health, house, etc.
    description = Column(Text, nullable=True)
    priority = Column(Integer, nullable=True)  # 1–5

    def __repr__(self):
        return f"<LifeRole(name={self.name}, domain={self.domain}, priority={self.priority})>"


class RoleCapacitySnapshot(Base):
    __tablename__ = "role_capacity_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    load_level = Column(Float, nullable=False)  # 0.0–1.0 how loaded you feel
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RoleCapacitySnapshot(role_id={self.role_id}, load_level={self.load_level})>"
