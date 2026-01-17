from sqlalchemy import Column, Integer, String, Float, DateTime, func
from ..core.db import Base

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)         # e.g., "fx_monthly_yield"
    value = Column(Float, nullable=False)                          # numeric value
    unit = Column(String(32), nullable=True)                       # e.g., "%", "USD"
    tags = Column(String(255), nullable=True)                      # csv tags, e.g., "engine:fx,scope:safe"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
