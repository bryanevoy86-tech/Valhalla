from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.db.base_class import Base
import datetime

class Legacy(Base):
    __tablename__ = "legacies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g. "Legacy-1", "Legacy-2"
    status = Column(String, default="active")  # active, pending, cloned
    readiness_score = Column(Integer, default=0)  # 0–100
    auto_clone_enabled = Column(Boolean, default=True)

    last_clone_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
