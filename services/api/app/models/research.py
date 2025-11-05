from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class ResearchSource(Base):
    """A source Heimdall can learn from (web page, repo, API, etc.)"""
    __tablename__ = "research_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    kind = Column(String(50), default="web")  # web, repo, api, file
    tags = Column(String(512), default="")  # comma-separated tags (added in v3_9)
    ttl_seconds = Column(Integer, default=86400)  # cache duration
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_ingested_at = Column(DateTime, nullable=True)

    # Relationship to documents
    docs = relationship("ResearchDoc", back_populates="source", cascade="all, delete-orphan")


class ResearchDoc(Base):
    """Ingested content from a source (cleaned text, chunks, etc.)"""
    __tablename__ = "research_docs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("research_sources.id"), nullable=False)
    title = Column(String(512), nullable=True)
    url = Column(String(2048), nullable=True)
    content = Column(Text, nullable=False)  # cleaned text
    chunk_index = Column(Integer, default=0)  # for splitting large docs
    ingested_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)  # JSON for extra fields
    embedding_json = Column(Text, nullable=True)  # JSON list of floats (vector)

    # Relationship
    source = relationship("ResearchSource", back_populates="docs")


class ResearchQuery(Base):
    """Log of queries Heimdall has made (for analytics/improvement)"""
    __tablename__ = "research_queries"

    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text, nullable=False)
    result_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)


class Playbook(Base):
    """Structured lessons/rules Heimdall can reference"""
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    title = Column(String(512), nullable=False)
    body_md = Column(Text, nullable=False)  # Markdown content
    tags = Column(String(512), nullable=True)  # comma-separated
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResearchPlaybook(Base):
    """Pack 8.1: Independent research playbooks storage (JSON-friendly fields)."""
    __tablename__ = "research_playbooks"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(200), unique=True, index=True, nullable=False)
    title = Column(String(300), nullable=False)
    steps = Column(Text, nullable=False)  # JSON string of steps array
    tags = Column(String(512), default="")  # comma-separated
    meta = Column(Text, default="{}")  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
