"""Private, segregated statement-fixture evidence."""
from sqlalchemy import Column, Date, Index, JSON, String, Uuid
from app.core.db import Base


class StatementAccount(Base):
    __tablename__ = "prime_statement_accounts"
    account_key = Column(String(64), primary_key=True)
    scope_key = Column(String(64), nullable=False)
    currency = Column(String(3), nullable=False)
    purpose = Column(String(18), nullable=False)
    head_id = Column(Uuid())


class StatementImport(Base):
    __tablename__ = "prime_statement_imports"
    __table_args__ = (Index("ix_statement_scope_account", "account_key", "period_end"),)
    id = Column(Uuid(), primary_key=True)
    account_key = Column(String(64), nullable=False)
    period_end = Column(Date(), nullable=False)
    digest = Column(String(64), nullable=False)
    payload = Column(JSON(), nullable=False)


class StatementEntry(Base):
    __tablename__ = "prime_statement_entries"
    key = Column(String(64), primary_key=True)
    statement_id = Column(Uuid(), nullable=False, index=True)
