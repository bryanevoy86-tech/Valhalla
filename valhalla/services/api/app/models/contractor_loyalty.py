from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
import datetime
from app.db.base_class import Base


class ContractorRank(Base):
    __tablename__ = "contractor_ranks"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    min_score = Column(Float, default=0.0)
    max_score = Column(Float, default=100.0)
    perks = Column(Text)


class ContractorLoyaltyVault(Base):
    __tablename__ = "contractor_loyalty_vaults"

    id = Column(Integer, primary_key=True, index=True)
    contractor_id = Column(Integer, nullable=False)
    contractor_name = Column(String, nullable=False)
    rank_code = Column(String, nullable=False)
    loyalty_score = Column(Float, default=0.0)
    vault_balance = Column(Float, default=0.0)
    jv_eligible = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
