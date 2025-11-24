from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, default="general")
    active = Column(Boolean, default=True)
    trigger_expression = Column(Text, nullable=False)
    action_expression = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

__all__ = ["AutomationRule"]
