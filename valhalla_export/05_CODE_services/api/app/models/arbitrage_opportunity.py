from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, DateTime, func, Text
from app.core.db import Base


class ArbitrageOpportunity(Base):
    __tablename__ = "arbitrage_opportunities"

    id = Column(Integer, primary_key=True)
    sku = Column(String(128), nullable=False)

    buy_source = Column(String(64), nullable=False)
    buy_price = Column(Float, nullable=False)
    buy_url = Column(String(512), nullable=True)

    sell_source = Column(String(64), nullable=False)
    sell_price = Column(Float, nullable=False)
    sell_url = Column(String(512), nullable=True)

    fees_estimate = Column(Float, nullable=False, default=0.0)
    shipping_estimate = Column(Float, nullable=False, default=0.0)

    gross_spread = Column(Float, nullable=False)           # sell - buy
    net_profit = Column(Float, nullable=False)             # gross - fees - shipping
    roi = Column(Float, nullable=False)                    # net / buy

    confidence = Column(Float, nullable=False, default=0.5)
    reason = Column(Text, nullable=True)

    status = Column(String(16), nullable=False, default="OPEN")  # OPEN | IGNORED | EXPIRED
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
