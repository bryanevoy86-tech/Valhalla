"""
PACK W: System Metadata Model
Stores system-level completion status and version information.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.models.base import Base


class SystemMetadata(Base):
    """Single-row table tracking overall system completion status."""

    __tablename__ = "system_metadata"

    id = Column(Integer, primary_key=True, index=True, default=1)
    
    # Semantic versioning: major.minor.patch
    version = Column(String, nullable=False, default="1.0.0")
    
    # Whether backend is considered complete
    backend_complete = Column(Boolean, default=False, nullable=False)
    
    # Human-readable notes about status
    notes = Column(String, nullable=True)
    
    # Track when metadata was last updated
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Track when backend was marked complete
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return (
            f"<SystemMetadata(id={self.id}, version={self.version}, "
            f"backend_complete={self.backend_complete}, updated_at={self.updated_at})>"
        )
