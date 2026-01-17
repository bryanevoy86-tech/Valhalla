"""
Pack 56: King's Hub + Adaptive Vault Scaling - ORM models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.core.db import Base

class KingProfile(Base):
    __tablename__ = "king_profile"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False, default="King")
    currency = Column(String(8), nullable=False, default="CAD")
    notes = Column(Text)

class KingVault(Base):
    __tablename__ = "king_vaults"
    id = Column(Integer, primary_key=True)
    label = Column(String(64), nullable=False)
    balance = Column(Numeric(14,2), nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="CAD")

class KingRule(Base):
    __tablename__ = "king_rules"
    id = Column(Integer, primary_key=True)
    active = Column(Boolean, nullable=False, default=True)
    rules_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class KingTxn(Base):
    __tablename__ = "king_txns"
    id = Column(Integer, primary_key=True)
    vault_id = Column(Integer, ForeignKey("king_vaults.id", ondelete="CASCADE"))
    kind = Column(String(24), nullable=False)
    amount = Column(Numeric(14,2), nullable=False)
    note = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())

class BahamasProgress(Base):
    __tablename__ = "bahamas_progress"
    id = Column(Integer, primary_key=True)
    target_amount = Column(Numeric(14,2), nullable=False, default=500000)
    monthly_min = Column(Numeric(14,2), nullable=False, default=5000)
    last_month_yyyymm = Column(String(7))
    status_note = Column(String(256))
