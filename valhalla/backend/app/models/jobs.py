from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.sql import func

from .base import Base


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=True)
    name = Column(String, nullable=False, index=True)
    args = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="queued")
    priority = Column(Integer, nullable=False, default=5)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    scheduled_at = Column(TIMESTAMP(timezone=True), index=True, server_default=func.now())
    started_at = Column(TIMESTAMP(timezone=True))
    finished_at = Column(TIMESTAMP(timezone=True))
    progress = Column(Integer, nullable=False, default=0)
    last_error = Column(String)
    created_by = Column(Integer, index=True, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)


class JobRun(Base):
    __tablename__ = "job_runs"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    started_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    finished_at = Column(TIMESTAMP(timezone=True))
    success = Column(Boolean, default=False, index=True)
    error = Column(String)
    logs = Column(JSON)


class DistLock(Base):
    __tablename__ = "dist_locks"
    key = Column(String, primary_key=True)
    owner = Column(String, nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), index=True)
