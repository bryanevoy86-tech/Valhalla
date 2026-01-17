"""
Pack 54: Children's Hubs + Vault Guardians - ORM models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.sql import func
from app.core.db import Base

class KidsHubChildProfile(Base):
    __tablename__ = "child_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    age = Column(Integer)
    guardian_name = Column(String(64))
    avatar_theme = Column(String(32))
    save_pct = Column(Float, nullable=False, default=0.20)
    invest_pct = Column(Float, nullable=False, default=0.00)
    notes = Column(Text)

class VaultGuardian(Base):
    __tablename__ = "vault_guardians"
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id", ondelete="CASCADE"))
    name = Column(String(64), nullable=False)
    personality = Column(String(32), nullable=False)
    lore = Column(Text)

class Chore(Base):
    __tablename__ = "chores"
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id", ondelete="CASCADE"))
    title = Column(String(128), nullable=False)
    freq = Column(String(16), nullable=False)
    coins = Column(Integer, nullable=False)
    active = Column(Boolean, nullable=False, default=True)

class ChoreLog(Base):
    __tablename__ = "chore_logs"
    id = Column(Integer, primary_key=True)
    chore_id = Column(Integer, ForeignKey("chores.id", ondelete="CASCADE"))
    completed_at = Column(DateTime, server_default=func.now())
    coins_awarded = Column(Integer, nullable=False)

class CoinWallet(Base):
    __tablename__ = "coin_wallets"
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id", ondelete="CASCADE"))
    spendable = Column(Integer, nullable=False, default=0)
    savings = Column(Integer, nullable=False, default=0)
    invested = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, server_default=func.now())

class CoinTxn(Base):
    __tablename__ = "coin_txns"
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id", ondelete="CASCADE"))
    kind = Column(String(24), nullable=False)
    amount = Column(Integer, nullable=False)
    memo = Column(String(256))
    created_at = Column(DateTime, server_default=func.now())

class WishlistItem(Base):
    __tablename__ = "wishlist_items"
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id", ondelete="CASCADE"))
    title = Column(String(128), nullable=False)
    priority = Column(Integer, nullable=False, default=3)
    coins_target = Column(Integer)

class IdeaSubmission(Base):
    __tablename__ = "idea_submissions"
    id = Column(Integer, primary_key=True)
    child_id = Column(Integer, ForeignKey("child_profiles.id", ondelete="CASCADE"))
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
