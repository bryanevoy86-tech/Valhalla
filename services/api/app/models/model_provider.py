"""
PACK CL12: Model Provider Registry
Keeps track of which AI model Heimdall is currently using.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from app.models.base import Base


class ModelProvider(Base):
    """
    Registry of available model backends (GPT versions, vendors, etc.).
    """

    __tablename__ = "model_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # e.g. "gpt-5.1-thinking"
    vendor = Column(String, nullable=False)             # e.g. "openai"
    description = Column(String, nullable=True)

    # Configuration details, like base URL, model ID, special flags, etc.
    config = Column(JSON, nullable=True)

    # Flags
    active = Column(Boolean, nullable=False, default=False)
    default_for_heimdall = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
