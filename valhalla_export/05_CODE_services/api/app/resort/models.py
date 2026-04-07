"""Pack 58: Resort Vault + Residency Timeline - Models"""
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text, DateTime, Date, Numeric, Float, ForeignKey
from sqlalchemy.sql import func
from app.core.db import Base

class ResortProject(Base):
    __tablename__ = "resort_projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    target_budget: Mapped[float] = mapped_column(Numeric(14,2), nullable=False, default=0)
    vault_balance: Mapped[float] = mapped_column(Numeric(14,2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="planning")
    notes: Mapped[str | None] = mapped_column(Text)

class ResortVaultTxn(Base):
    __tablename__ = "resort_vault_txns"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("resort_projects.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(24))
    amount: Mapped[float] = mapped_column(Numeric(14,2))
    note: Mapped[str | None] = mapped_column(String(256))
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())

class ResortMilestone(Base):
    __tablename__ = "resort_milestones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("resort_projects.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    due_date: Mapped[str | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    percent: Mapped[float] = mapped_column(Float, nullable=False, default=0)

class ResortQuote(Base):
    __tablename__ = "resort_quotes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("resort_projects.id", ondelete="CASCADE"))
    vendor: Mapped[str] = mapped_column(String(128), nullable=False)
    scope: Mapped[str] = mapped_column(String(256), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(14,2))
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="received")

class ResortFunding(Base):
    __tablename__ = "resort_funding"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("resort_projects.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    program_name: Mapped[str | None] = mapped_column(String(128))
    amount: Mapped[float] = mapped_column(Numeric(14,2))
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="prospect")

class ResidencyTimeline(Base):
    __tablename__ = "residency_timeline"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country: Mapped[str] = mapped_column(String(64), nullable=False)
    target_date: Mapped[str | None] = mapped_column(Date)
    min_capital: Mapped[float] = mapped_column(Numeric(14,2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="planning")
    note: Mapped[str | None] = mapped_column(Text)

class ResidencyStep(Base):
    __tablename__ = "residency_steps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timeline_id: Mapped[int] = mapped_column(Integer, ForeignKey("residency_timeline.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    due_date: Mapped[str | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    percent: Mapped[float] = mapped_column(Float, nullable=False, default=0)
