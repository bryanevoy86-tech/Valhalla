"""
Pack 50: Full Accounting Suite - ORM models
"""
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Numeric, Float, Text
from sqlalchemy.sql import func
from app.core.db import Base


class Account(Base):
    __tablename__ = "acct_accounts"
    id = Column(Integer, primary_key=True)
    code = Column(String(24), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    type = Column(String(24), nullable=False)  # asset|liability|equity|income|expense
    currency = Column(String(8), nullable=False, default="CAD")
    active = Column(Boolean, nullable=False, default=True)


class Period(Base):
    __tablename__ = "acct_periods"
    id = Column(Integer, primary_key=True)
    label = Column(String(32), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    closed = Column(Boolean, nullable=False, default=False)


class JournalEntry(Base):
    __tablename__ = "acct_journal_entries"
    id = Column(Integer, primary_key=True)
    entry_date = Column(Date, nullable=False)
    memo = Column(String(256))
    source = Column(String(64))
    source_ref = Column(String(128))
    created_at = Column(DateTime, server_default=func.now())


class JournalLine(Base):
    __tablename__ = "acct_journal_lines"
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey("acct_journal_entries.id", ondelete="CASCADE"))
    account_id = Column(Integer, ForeignKey("acct_accounts.id", ondelete="RESTRICT"))
    debit = Column(Numeric(14,2), nullable=False, default=0)
    credit = Column(Numeric(14,2), nullable=False, default=0)
    tax_code = Column(String(32))
    tag = Column(String(64))


class TaxRule(Base):
    __tablename__ = "acct_tax_rules"
    id = Column(Integer, primary_key=True)
    code = Column(String(32), unique=True, nullable=False)
    rate_pct = Column(Float, nullable=False)
    applies_to = Column(String(24), nullable=False)
    jurisdiction = Column(String(24))


class TaxCategory(Base):
    __tablename__ = "acct_tax_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    risk_weight = Column(Float, nullable=False, default=0.5)


class TaxMapping(Base):
    __tablename__ = "acct_tax_mappings"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("acct_accounts.id", ondelete="CASCADE"))
    tax_category_id = Column(Integer, ForeignKey("acct_tax_categories.id", ondelete="CASCADE"))


class ReportRow(Base):
    __tablename__ = "acct_reports"
    id = Column(Integer, primary_key=True)
    kind = Column(String(24), nullable=False)
    period_label = Column(String(32), nullable=False)
    payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class CRABotRun(Base):
    __tablename__ = "cra_bot_runs"
    id = Column(Integer, primary_key=True)
    period_label = Column(String(32), nullable=False)
    risk_score = Column(Float, nullable=False)
    summary = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
