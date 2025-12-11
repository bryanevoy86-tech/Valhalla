"""
PACK AO: Explainability Engine Model
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from app.models.base import Base


class ExplanationLog(Base):
    __tablename__ = "explanation_logs"

    id = Column(Integer, primary_key=True, index=True)

    context_type = Column(String, nullable=False)  # scorecard, audit, decision, contract
    context_id = Column(String, nullable=True)     # id of the entity

    explanation = Column(Text, nullable=False)     # human-readable text
    metadata = Column(JSON, nullable=True)         # structured breadcrumbs

    created_at = Column(DateTime, default=datetime.utcnow)
