from sqlalchemy import JSON, TIMESTAMP, Column, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from ..core.db import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    kind = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    src_filename = Column(String, nullable=False)
    options = Column(JSON, nullable=True)
    total_rows = Column(Integer, nullable=True)
    success_rows = Column(Integer, nullable=True, default=0)
    error_rows = Column(Integer, nullable=True, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)


class ImportRowError(Base):
    __tablename__ = "import_row_errors"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True)
    row_number = Column(Integer, nullable=False)
    data = Column(JSON, nullable=True)
    error = Column(Text, nullable=False)


class ExportJob(Base):
    __tablename__ = "export_jobs"
    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True, nullable=False)
    kind = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    filters = Column(JSON, nullable=True)
    out_filename = Column(String, nullable=True)
    file_type = Column(String, nullable=True)  # MIME type for preview
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
