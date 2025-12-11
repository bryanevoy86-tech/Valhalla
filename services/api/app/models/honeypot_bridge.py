"""
PACK TS: Honeypot Registry & Telemetry Bridge Models
Manages honeypot instances and collects attack telemetry.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.models.base import Base


class HoneypotInstance(Base):
    __tablename__ = "honeypot_instances"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    name = Column(String, nullable=False, index=True)
    api_key = Column(String, nullable=False, unique=True, index=True)
    location = Column(String, nullable=True)         # geographic or logical location
    honeypot_type = Column(String, nullable=False)   # ssh, web, database, custom
    active = Column(Boolean, default=True)
    metadata = Column(JSON, nullable=True)           # version, credentials, config
    
    # Relationships
    events = relationship("HoneypotEvent", cascade="all, delete-orphan", back_populates="instance")


class HoneypotEvent(Base):
    __tablename__ = "honeypot_events"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    honeypot_id = Column(Integer, ForeignKey("honeypot_instances.id"), nullable=False, index=True)
    source_ip = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)      # connection, auth_attempt, exploitation, scan
    payload = Column(JSON, nullable=True)            # request/response/command details
    detected_threat = Column(String, nullable=True)  # classification
    processed = Column(Boolean, default=False)
    
    # Relationships
    instance = relationship("HoneypotInstance", back_populates="events")
