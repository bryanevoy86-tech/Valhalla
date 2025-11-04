from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from backend.app.core.db import Base

class ExportJob(Base):
    __tablename__ = "export_jobs"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=True)
    status = Column(String, nullable=False, default="queued", index=True)
    progress = Column(Integer, nullable=False, default=0)
    progress_msg = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), index=True, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    # Add other fields as needed (job_type, payload, etc.)
