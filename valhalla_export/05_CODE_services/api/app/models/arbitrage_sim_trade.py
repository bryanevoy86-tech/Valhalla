from __future__ import annotations

from sqlalchemy import Column, Integer, String, Float, DateTime, func, Text
from app.core.db import Base


class ArbitrageSimTrade(Base):
    """
    Paper-trading ledger for arbitrage.
    Phase A uses SIM trades only.
    """
    __tablename__ = "arbitrage_sim_trades"

    id = Column(Integer, primary_key=True)
    sku = Column(String(128), nullable=False)

    buy_price = Column(Float, nullable=False)
    sell_price = Column(Float, nullable=False)

    fees = Column(Float, nullable=False, default=0.0)
    shipping = Column(Float, nullable=False, default=0.0)

    net_profit = Column(Float, nullable=False)
    roi = Column(Float, nullable=False)

    linked_opportunity_id = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
