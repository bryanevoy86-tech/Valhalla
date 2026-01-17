from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)

    category = Column(String, default="general")  # "legal", "tax", "ops", "family", etc.
    assignee = Column(String, default="king")     # "king", "queen", "heimdall", "va-team", etc.

    status = Column(String, default="pending")    # pending / in-progress / done / blocked
    priority = Column(Integer, default=5)           # 1 (highest) to 10 (lowest)

    due_at = Column(DateTime)
    completed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
