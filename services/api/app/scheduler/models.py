from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timezone
from app.core.db import Base


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    cron_expr = Column(String, nullable=False)  # e.g. "0 * * * *" (hourly)
    last_run = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ScheduledJob(name={self.name}, active={self.active})>"
