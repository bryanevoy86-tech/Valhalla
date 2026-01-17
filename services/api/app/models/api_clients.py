"""
PACK UD: API Key & Client Registry Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.models.base import Base


class ApiClient(Base):
    __tablename__ = "api_clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    client_type = Column(String, nullable=False)
    api_key = Column(String, nullable=False, unique=True)
    active = Column(Boolean, nullable=False, default=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
