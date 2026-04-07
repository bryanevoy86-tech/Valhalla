"""Revenue ledger - immutable record of all revenue events."""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class RevenueEntry(Base):
    """Immutable revenue event record."""
    __tablename__ = "revenue_ledger"
    
    id = Column(String, primary_key=True)
    engine = Column(String, nullable=False, index=True)  # Which engine generated this
    amount = Column(Integer, nullable=False)  # Amount in cents
    source = Column(String, nullable=False)  # Where the revenue came from (contract, deal, etc)
    meta = Column(String, nullable=True)  # JSON-like metadata
    created_at = Column(DateTime, server_default=func.now(), index=True)
