"""Private economic mandate state and append-only decision evidence."""
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Integer, JSON, String, UniqueConstraint, Uuid
from app.core.db import Base


class EconomicPool(Base):
    __tablename__ = "prime_economic_pools"
    __table_args__ = (CheckConstraint("committed_minor >= 0", name="ck_economic_pool_commit"),)
    currency = Column(String(3), primary_key=True)
    committed_minor = Column(BigInteger(), nullable=False, default=0)
    sequence = Column(Integer(), nullable=False, default=0)
    liquidity_id = Column(Uuid())
    liquidity_conflict = Column(Boolean(), nullable=False, default=False)


class EconomicOperation(Base):
    __tablename__ = "prime_economic_operations"
    scope_key = Column(String(64), primary_key=True)
    scope = Column(JSON(), nullable=False)
    currency = Column(String(3), nullable=False)
    sequence = Column(Integer(), nullable=False, default=0)


class EconomicRecord(Base):
    __tablename__ = "prime_economic_records"
    __table_args__ = (UniqueConstraint("scope_key", "sequence", name="uq_economic_record_sequence"),)
    id = Column(Uuid(), primary_key=True)
    scope_key = Column(String(64), nullable=False, index=True)
    sequence = Column(Integer(), nullable=False)
    kind = Column(String(18), nullable=False)
    receipt_key = Column(String(64), unique=True)
    payload = Column(JSON(), nullable=False)
    digest = Column(String(64), nullable=False)
