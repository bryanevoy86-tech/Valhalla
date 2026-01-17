"""
PACK AR: Heimdall Workload Balancer Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from app.models.base import Base


class HeimdallJob(Base):
    __tablename__ = "heimdall_jobs"

    id = Column(Integer, primary_key=True, index=True)

    job_type = Column(String, nullable=False)      # research, write_email, analyze_deal, story, etc.
    source = Column(String, nullable=True)         # user, system, timer, kid_hub, etc.

    priority = Column(String, nullable=False, default="normal")  # low, normal, high, critical
    status = Column(
        String,
        nullable=False,
        default="queued",     # queued, in_progress, completed, cancelled, failed
    )

    payload = Column(JSON, nullable=True)          # parameters Heimdall will use

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class HeimdallWorkloadConfig(Base):
    """
    Configuration level: which job types are enabled / disabled, max concurrent, etc.
    """
    __tablename__ = "heimdall_workload_config"

    id = Column(Integer, primary_key=True, index=True)

    job_type = Column(String, nullable=False, unique=True)
    enabled = Column(Boolean, default=True)
    max_concurrent = Column(Integer, nullable=True)   # optional, for future worker logic
    notes = Column(String, nullable=True)

    updated_at = Column(DateTime, default=datetime.utcnow)
