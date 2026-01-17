from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.models.base import Base


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)            # "weekly_empire_snapshot"
    category = Column(String, default="general")     # "kpi", "snapshot", "legal", etc.
    active = Column(Boolean, default=True)

    # cron-like string or simple JSON expression, your choice
    schedule = Column(String, nullable=False)        # e.g. "0 3 * * MON" or "daily@03:00"

    task_path = Column(String, nullable=False)
    # Python path or identifier for worker to execute, e.g. "tasks.snapshots.create_weekly"

    args = Column(Text)                              # JSON payload (string)
    last_run_at = Column(DateTime)
    last_status = Column(String)                     # "success", "failed", etc.
    last_error = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
