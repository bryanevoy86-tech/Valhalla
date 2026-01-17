from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from app.core.db import Base


class EngineStateRow(Base):
    __tablename__ = "engine_states"
    __table_args__ = (UniqueConstraint("engine_name", name="uq_engine_states_engine_name"),)

    id = Column(Integer, primary_key=True, index=True)
    engine_name = Column(String(64), nullable=False, index=True)
    state = Column(String(16), nullable=False, default="DORMANT")
    changed_by = Column(String(128), nullable=True)
    reason = Column(String(512), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
