"""
PACK L0-09: Strategic Event Model
Records strategic events from various modules for long-term memory.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Index

from app.models.base import Base


class StrategicEvent(Base):
    """
    Records important strategic events for system observability and long-term memory.
    
    Examples:
    - Mode changes (growth -> conservative -> recovery)
    - Major decisions executed or rejected
    - Deal closures
    - Rule changes
    - Crisis events
    - Significant achievements
    
    Marked as stable schema (STABLE CONTRACT).
    """
    
    __tablename__ = "strategic_events"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    
    # Event classification
    source = Column(String(100), nullable=False)  # "mode_engine", "decision_engine", "job_runner", etc.
    category = Column(String(50), nullable=False, index=True)  # "mode_change", "decision", "deal", "rule", "crisis", "win", etc.
    label = Column(String(200), nullable=False)  # Human-readable label
    
    # Structured payload
    payload = Column(JSON, nullable=True)  # Context data: {old_mode, new_mode, reason, metrics, etc.}
    
    # Importance for prioritization
    importance_score = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index("idx_tenant_timestamp", "tenant_id", "timestamp"),
        Index("idx_source_category", "source", "category"),
        Index("idx_importance", "importance_score"),
    )
    
    def __repr__(self) -> str:
        return f"<StrategicEvent(id={self.id}, tenant_id={self.tenant_id}, category={self.category}, label={self.label})>"
