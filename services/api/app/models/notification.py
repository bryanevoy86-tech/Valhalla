from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, default="system")
    audience = Column(String, default="king")
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String, default="info")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    read_at = Column(DateTime)

__all__ = ["Notification"]
