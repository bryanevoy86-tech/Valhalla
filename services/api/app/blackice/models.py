"""
Pack 53: Black Ice Tier II + Shadow Contingency - ORM models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base

class BlackIceProtocol(Base):
    __tablename__ = "black_ice_protocols"
    id = Column(Integer, primary_key=True)
    level = Column(Integer, nullable=False, default=2)
    name = Column(String(64), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class ContingencyEvent(Base):
    __tablename__ = "contingency_events"
    id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey("black_ice_protocols.id", ondelete="CASCADE"))
    event_type = Column(String(32), nullable=False)
    details = Column(Text)
    occurred_at = Column(DateTime, server_default=func.now())

class KeyRotationCheck(Base):
    __tablename__ = "key_rotation_checks"
    id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey("black_ice_protocols.id", ondelete="CASCADE"))
    checklist_item = Column(String(64), nullable=False)
    checked = Column(Boolean, nullable=False, default=False)
    checked_at = Column(DateTime, server_default=func.now())

class ContinuityWindow(Base):
    __tablename__ = "continuity_windows"
    id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey("black_ice_protocols.id", ondelete="CASCADE"))
    min_hours = Column(Integer, nullable=False, default=72)
    alert_channel = Column(String(32), nullable=False, default="ops")
    active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text)
