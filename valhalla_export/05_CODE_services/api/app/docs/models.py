from sqlalchemy import Column, Integer, String, JSON, DateTime, Text
from datetime import datetime, timezone
from app.core.db import Base


class DocTemplate(Base):
    __tablename__ = "doc_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # e.g., "Assignment Contract v1"
    description = Column(String, nullable=True)
    content = Column(Text, nullable=False)  # text with {{placeholders}}
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class GeneratedDoc(Base):
    __tablename__ = "generated_docs"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, nullable=False)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # rendered text (HTML or plain)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
