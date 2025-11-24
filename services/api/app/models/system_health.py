from sqlalchemy import Column, Integer, String, DateTime
import datetime
from app.core.db import Base


class SystemHealth(Base):
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, nullable=False, unique=True)
    status = Column(String, default="unknown")
    last_heartbeat = Column(DateTime)
    issue_count = Column(Integer, default=0)
    notes = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


__all__ = ["SystemHealth"]
