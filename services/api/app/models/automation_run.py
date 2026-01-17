from sqlalchemy import Column, Integer, String, DateTime, Text
from app.db.base_class import Base
import datetime


class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, nullable=False)  # link to automation_rules.id (logical)
    rule_name = Column(String, nullable=False)  # denormalized for quick lookup

    status = Column(String, default="started")  # started / success / failed / skipped
    severity = Column(String, default="info")  # info / warn / critical

    input_snapshot = Column(Text)  # state before action (optional)
    action_result = Column(Text)  # what action did / returned (optional)
    error_message = Column(Text)  # if failed

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime)
