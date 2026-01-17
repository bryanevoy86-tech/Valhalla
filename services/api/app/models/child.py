from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime

class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    nickname = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    chores = relationship("Chore", back_populates="child")
    coin_entries = relationship("CoinLedger", back_populates="child")

class Chore(Base):
    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(String)
    coin_value = Column(Float, default=0.0)
    frequency = Column(String, default="ad-hoc")
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    child = relationship("Child", back_populates="chores")

class CoinLedger(Base):
    __tablename__ = "coin_ledger"

    id = Column(Integer, primary_key=True, index=True)
    child_id = Column(Integer, ForeignKey("children.id"), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(String)
    entry_type = Column(String, default="earn")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    child = relationship("Child", back_populates="coin_entries")
