from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from app.db.base_class import Base
import datetime


class FunFundRouting(Base):
    __tablename__ = "funfund_routing"

    id = Column(Integer, primary_key=True, index=True)
    profile_name = Column(String, nullable=False, unique=True)   # "default", "aggressive-arb"

    # percent of Fun Fund routed automatically into arbitrage engine
    arbitrage_percent = Column(Float, default=1.0)  # 0.0–1.0 (1.0 = 100%)

    # min + max liquid balance you want to keep in the Fun Fund account
    min_liquid_balance = Column(Float, default=0.0)
    max_liquid_balance = Column(Float, default=1_000_000.0)

    # how aggressive the arbitrage can be (your own config scale)
    risk_profile = Column(String, default="moderate")  # conservative/moderate/aggressive

    active = Column(Boolean, default=True)
    description = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
