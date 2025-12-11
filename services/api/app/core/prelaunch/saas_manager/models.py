"""SaaS Manager Models - Multi-tenant support"""
from datetime import datetime
from sqlalchemy import Column, DateTime, String, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class Tenant(Base):
    """Multi-tenant account for SaaS mode."""
    __tablename__ = "saas_tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    contact_email = Column(String(255), nullable=False)
    plan = Column(String(32), default="STARTER")
    status = Column(String(32), default="TRIAL")
    usage = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
