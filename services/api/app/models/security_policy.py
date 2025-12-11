"""
PACK TQ: Security Policy & Blocklist Models
Owned by Tyr: defines global security behavior and block rules.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime

from app.models.base import Base


class SecurityPolicy(Base):
    __tablename__ = "security_policies"

    id = Column(Integer, primary_key=True, index=True)
    default_mode = Column(String, nullable=False, default="normal")  # normal/elevated/lockdown
    auto_elevate_on_incidents = Column(Boolean, nullable=False, default=True)
    auto_lockdown_on_critical = Column(Boolean, nullable=False, default=True)
    max_failed_auth_per_minute = Column(Integer, nullable=False, default=10)
    max_scan_events_per_minute = Column(Integer, nullable=False, default=20)
    notes = Column(Text, nullable=True)


class BlockedEntity(Base):
    __tablename__ = "blocked_entities"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)  # ip, user, api_key
    value = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
