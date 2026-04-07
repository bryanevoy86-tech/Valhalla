from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import datetime
from app.models.base import Base


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    url = Column(String)
    source_type = Column(String, default="web")
    engines = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    priority = Column(Integer, default=5)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
