from sqlalchemy import Column, Integer, String, DateTime
from app.db.base_class import Base
import datetime

class ShieldEvent(Base):
    __tablename__ = "shield_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)  # income_drop, risk_alert, separation_trigger
    severity = Column(String, default="low")     # low / med / high
    description = Column(String)
    resolved = Column(String, default="pending")

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
