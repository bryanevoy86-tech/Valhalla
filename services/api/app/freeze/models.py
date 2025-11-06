from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from datetime import datetime, timezone
from app.core.db import Base


class FreezeRule(Base):
    __tablename__ = "freeze_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "drawdown_guard"
    metric = Column(String, nullable=False)  # e.g., "fx_drawdown_pct"
    threshold = Column(Float, nullable=False)  # e.g., 2.0
    comparator = Column(String, default=">")  # ">", "<", ">=", "<="
    active = Column(Boolean, default=True)
    scope = Column(String, nullable=True)  # "arbitrage", "all"


class FreezeEvent(Base):
    __tablename__ = "freeze_events"
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String, nullable=False)
    triggered_value = Column(Float, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved = Column(Boolean, default=False)
