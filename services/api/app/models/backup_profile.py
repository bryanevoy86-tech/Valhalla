from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class BackupProfile(Base):
    __tablename__ = "backup_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    target_type = Column(String, nullable=False)
    target_identifier = Column(String, nullable=False)
    frequency = Column(String, default="daily")
    retention_days = Column(Integer, default=30)
    encrypted = Column(Boolean, default=True)
    encryption_profile = Column(String)
    offsite_copy = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
