"""
PACK UH: Export & Snapshot Job Engine Models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.models.base import Base


class ExportJob(Base):
    __tablename__ = "export_jobs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    job_type = Column(String, nullable=False)
    filter_params = Column(JSON, nullable=True)
    status = Column(String, nullable=False, default="pending")
    storage_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    requested_by = Column(String, nullable=True)
