from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class AIPersona(Base):
    __tablename__ = "ai_personas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)     # "Heimdall", "Loki", etc.
    code = Column(String, nullable=False, unique=True)     # "heimdall", "loki", "valkyrie"
    role = Column(String, nullable=False)                  # "guardian", "checker", "closer"
    domain = Column(String, nullable=False)                # "empire", "legal", "sales", "training"

    status = Column(String, default="active")              # active / paused / archived
    description = Column(Text)                             # persona description, voice, etc.
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
