"""Contract Engine Upgrade Models"""
from datetime import datetime
from sqlalchemy import Column, DateTime, JSON, String
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.models.base import Base


class ContractTemplate(Base):
    """Contract templates for various categories."""
    __tablename__ = "contract_templates_prelaunch"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(64), nullable=False)  # real_estate / contractor / saas / other
    language = Column(String(8), default="en")
    body = Column(String, nullable=False)
    template_metadata = Column(JSON, nullable=True)  # avoid reserved keyword

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ContractReview(Base):
    """Contract reviews with red flag detection."""
    __tablename__ = "contract_reviews_prelaunch"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(64), nullable=False)  # uploaded / external / generated
    category = Column(String(64), nullable=True)
    text = Column(String, nullable=False)
    red_flags = Column(JSON, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
