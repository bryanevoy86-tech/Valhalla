"""
PACK L0-05: System Status Model
Tracks overall system status, completion state, and version information.
Marked as stable schema (STABLE CONTRACT).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, Text

from app.models.base import Base


class SystemMetadata(Base):
    """
    Singleton system metadata (id=1).
    Tracks version, completion status, and system-wide configuration.
    """
    
    __tablename__ = "system_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Version tracking
    version = Column(String(50), nullable=False, default="0.1.0")
    backend_complete = Column(Boolean, default=False, index=True)
    
    # Status summary
    overall_status = Column(String(20), default="initializing")  # "initializing", "operational", "degraded"
    
    # Pack registry (16 packs tracked here as JSON)
    packs_registry = Column(JSON, nullable=True)  # e.g., {"L0-05": {"status": "complete", "updated_at": "..."}}
    
    # Configuration and notes
    notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class PackInfo(Base):
    """
    Individual pack information for the 16 packs.
    """
    
    __tablename__ = "pack_info"
    
    id = Column(String(10), primary_key=True)  # "L0-05", "L0-06", etc.
    status = Column(String(20), default="not_started", index=True)  # "not_started", "in_progress", "complete", "stable"
    description = Column(String(500), nullable=True)
    endpoints_count = Column(Integer, default=0)
    models_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
