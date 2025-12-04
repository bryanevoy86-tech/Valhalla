from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from app.db.base_class import Base
import datetime


class SystemCheckJob(Base):
    __tablename__ = "system_check_jobs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    scope = Column(String, nullable=False)
    scope_code = Column(String)
    schedule = Column(String, default="weekly")
    active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    last_status = Column(String)
    last_health_score = Column(Float, default=1.0)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
