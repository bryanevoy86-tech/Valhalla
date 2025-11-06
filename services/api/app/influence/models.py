"""
Influence Library models: techniques and cognitive biases.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.db import Base


class InfluenceTechnique(Base):
    __tablename__ = "influence_techniques"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CognitiveBias(Base):
    __tablename__ = "cognitive_biases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    mitigation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
