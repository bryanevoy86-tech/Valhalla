from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.db import Base


class BankConnection(Base):
    __tablename__ = "bank_connections"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)  # e.g., "plaid", "stripe"
    access_token = Column(String, nullable=True)  # store vault reference, not raw tokens in prod
    status = Column(String, default="disconnected")  # connected|disconnected|error
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("bank_connections.id"))
    name = Column(String, nullable=False)
    mask = Column(String, nullable=True)  # ****1234
    currency = Column(String, default="CAD")
    balance = Column(Float, default=0.0)
    type = Column(String, default="checking")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    connection = relationship("BankConnection", backref="accounts")


class ESignEnvelope(Base):
    __tablename__ = "esign_envelopes"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=False)  # e.g., "docusign"
    subject = Column(String, nullable=False)
    status = Column(String, default="created")  # created|sent|completed|voided
    recipients = Column(JSON, nullable=False)  # [{"email":"x@y", "name":"..."}]
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class VaultBalance(Base):
    __tablename__ = "vault_balances"
    id = Column(Integer, primary_key=True, index=True)
    vault_code = Column(String, nullable=False)  # e.g., "MAIN", "RESERVES", "FUN"
    currency = Column(String, default="CAD")
    balance = Column(Float, default=0.0)
    last_source = Column(String, nullable=True)  # "bank:12", "fx_engine"
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
