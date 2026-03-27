"""
Contract model - Direct mapping to contracts table from db_bootstrap.py
Represents signed/draft contracts linking to deals and offers.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from ..core.db import Base


class SimpleContract(Base):
    """
    Contract record linking deals and offers with signing status.
    This model maps directly to the contracts table created by db_bootstrap.py.
    """
    
    __tablename__ = "contracts"
    __table_args__ = {'extend_existing': True}  # Allow re-definition if table exists
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Foreign keys to deals and offers
    deal_id = Column(Integer, ForeignKey("deals.id"), nullable=True, index=True)
    offer_id = Column(Integer, ForeignKey("offers.id"), nullable=True, index=True)
    
    # Contract lifecycle
    status = Column(String(50), nullable=False, default="draft")
    template_id = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    pdf_url = Column(String(512), nullable=True)
    signing_status = Column(String(50), nullable=True)
    docusign_id = Column(String(255), nullable=True)
    
    # Can add relationships if needed
    # deal = relationship("Deal", back_populates="contracts")
    # offer = relationship("Offer", back_populates="contract")
