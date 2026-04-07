from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class ArbitrageProfile(Base):
    __tablename__ = "arbitrage_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)     # "default_fun_fund", "treasury"

    # which pool this is tuned for
    pool_type = Column(String, nullable=False)             # "fun_fund", "treasury"

    # risk / liquidity sliders 0–1 (internal to logic)
    risk_level = Column(Float, default=0.3)
    liquidity_priority = Column(Float, default=0.9)

    # caps as fraction of balance (0–1)
    max_exposure_fraction = Column(Float, default=0.5)     # how much can be deployed at once
    min_cash_buffer_fraction = Column(Float, default=0.2)  # always keep at least this in cash

    auto_trading_enabled = Column(Boolean, default=True)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )
