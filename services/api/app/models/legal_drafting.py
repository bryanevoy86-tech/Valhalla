"""PACK 91: Legal Drafting Engine
Drafts legal templates, documents, resolutions, notices.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.models.base import Base


class LegalTemplate(Base):
    __tablename__ = "legal_template"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class LegalDraft(Base):
    __tablename__ = "legal_draft"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, nullable=False)
    filled_payload = Column(Text, nullable=False)
    output_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
