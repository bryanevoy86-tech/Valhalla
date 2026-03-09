"""
PACK AI: Scenario Simulator Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)

    key = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    created_by = Column(String, nullable=True)   # user id, role, or "heimdall"
    created_at = Column(DateTime, default=datetime.utcnow)


class ScenarioRun(Base):
    __tablename__ = "scenario_runs"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, nullable=False)

    # Inputs and outputs are stored as JSON strings
    input_payload = Column(Text, nullable=True)
    result_payload = Column(Text, nullable=True)

    status = Column(
        String,
        nullable=False,
        default="pending",  # pending, running, completed, failed
    )
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
