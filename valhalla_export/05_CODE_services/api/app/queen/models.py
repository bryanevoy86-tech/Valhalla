"""
Pack 55: Queen's Hub + Fun Fund Vaults - ORM models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, Float
from sqlalchemy.sql import func
from app.core.db import Base

class QueenProfile(Base):
    __tablename__ = "queen_profile"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    email = Column(String(128))
    currency = Column(String(8), nullable=False, default="CAD")
    phase = Column(Integer, nullable=False, default=2)
    cap_month = Column(Numeric(14, 2), nullable=False, default=10000)
    tax_rate = Column(Float, nullable=False, default=0.18)
    notes = Column(Text)

class QueenVault(Base):
    __tablename__ = "queen_vaults"
    id = Column(Integer, primary_key=True)
    label = Column(String(64), nullable=False)
    balance = Column(Numeric(14, 2), nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="CAD")

class QueenVaultTxn(Base):
    __tablename__ = "queen_vault_txns"
    id = Column(Integer, primary_key=True)
    vault_id = Column(Integer, ForeignKey("queen_vaults.id", ondelete="CASCADE"))
    kind = Column(String(24), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    category = Column(String(64))
    note = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())

class QueenMonthCap(Base):
    __tablename__ = "queen_month_caps"
    id = Column(Integer, primary_key=True)
    yyyymm = Column(String(7), nullable=False)
    allowed = Column(Numeric(14, 2), nullable=False)
    used = Column(Numeric(14, 2), nullable=False, default=0)
    phase = Column(Integer, nullable=False)
