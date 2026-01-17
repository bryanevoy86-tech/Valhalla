"""Safe Browser Models - Kids Safe Browser Proxy"""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Index
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class KidBrowserHistory(Base):
    """Kids safe browser search and navigation history."""
    
    __tablename__ = "kid_browser_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    query = Column(String, nullable=True)
    url = Column(String, nullable=True)
    title = Column(String, nullable=True)
    result_type = Column(String(64), nullable=True)  # article / video / learning / search / etc.
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("ix_kid_browser_history_child_id", "child_id"),
        Index("ix_kid_browser_history_created_at", "created_at"),
    )
