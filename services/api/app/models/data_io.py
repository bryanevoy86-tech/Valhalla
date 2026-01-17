"""PACK 74: Data Import/Export Engine
Data IO operations for bulk import/export.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from app.models.base import Base


class ImportJob(Base):
    __tablename__ = "import_job"

    id = Column(Integer, primary_key=True, index=True)
    target_model = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, default="pending")
    error_report = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExportJob(Base):
    __tablename__ = "export_job"

    id = Column(Integer, primary_key=True, index=True)
    source_model = Column(String, nullable=False)
    filter_payload = Column(Text, nullable=True)
    status = Column(String, default="pending")
    download_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
