from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text, JSON, func
from datetime import datetime, timezone
from typing import Any, Optional
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



