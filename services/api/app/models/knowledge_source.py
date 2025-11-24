from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    url = Column(String)
    category = Column(String)
    priority = Column(Integer, default=10)
    active = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

__all__ = ["KnowledgeSource"]
