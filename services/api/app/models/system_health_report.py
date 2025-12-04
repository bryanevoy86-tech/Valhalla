from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class SystemHealthReport(Base):
    __tablename__ = "system_health_reports"

    id = Column(Integer, primary_key=True, index=True)
    run_at = Column(DateTime, default=datetime.datetime.utcnow)
    period_label = Column(String, nullable=False)
    errors_count = Column(Integer, default=0)
    critical_errors = Column(Integer, default=0)
    failed_automations = Column(Integer, default=0)
    unresolved_compliance_signals = Column(Integer, default=0)
    all_green = Column(Boolean, default=False)
    summary = Column(Text)
    notes = Column(Text)
