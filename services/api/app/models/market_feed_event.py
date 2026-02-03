from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, DateTime, func, Text
from app.core.db import Base


class MarketFeedEvent(Base):
    """
    Normalized 'inbox' for any future arbitrage data source.
    You can populate this manually now, then later via importers/APIs.
    """
    __tablename__ = "market_feed_events"

    id = Column(Integer, primary_key=True)
    source = Column(String(64), nullable=False)            # e.g. "ebay", "facebook", "kijiji", "manual"
    sku = Column(String(128), nullable=False)              # product identifier (your canonical key)
    title = Column(String(256), nullable=True)

    venue = Column(String(64), nullable=False)             # "BUY" venue or "SELL" venue context
    price = Column(Float, nullable=False)
    currency = Column(String(8), nullable=False, default="CAD")

    url = Column(String(512), nullable=True)
    raw_json = Column(Text, nullable=True)

    observed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
