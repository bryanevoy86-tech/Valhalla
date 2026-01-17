from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from app.core.db import Base


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String, nullable=False)  # url | file | note
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    tags = Column(String, nullable=True)  # comma-separated
    expires_at = Column(DateTime, nullable=True)  # TTL expiry
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
