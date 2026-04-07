"""
PACK SD: Credit Card & Spending Framework
Neutral organizational module for credit cards and spending rules.
Does not provide financial or tax advice - only organizes user-defined rules.
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.db import Base


class CreditCardProfile(Base):
    """
    Credit card profile with user-defined categories and restrictions.
    Neutral storage - no recommendations.
    """
    __tablename__ = "credit_card_profiles"

    id = Column(Integer, primary_key=True)
    card_id = Column(String(255), unique=True, nullable=False)
    nickname = Column(String(255), nullable=False)
    issuer = Column(String(255), nullable=True)
    card_type = Column(String(100), nullable=False)  # business, personal, travel, etc.
    status = Column(String(50), nullable=False, server_default="active")
    
    # Allowed and restricted categories as JSON
    allowed_categories = Column(JSON, nullable=True)  # [{category, notes}]
    restricted_categories = Column(JSON, nullable=True)  # [{category, notes}]
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    spending_rules = relationship("SpendingRule", back_populates="card")
    transactions = relationship("SpendingTransaction", back_populates="card")


class SpendingRule(Base):
    """
    User-defined spending rules for categorizing purchases.
    Applies your categories - does not determine tax eligibility.
    """
    __tablename__ = "spending_rules"

    id = Column(Integer, primary_key=True)
    rule_id = Column(String(255), unique=True, nullable=False)
    card_id = Column(Integer, ForeignKey("credit_card_profiles.id"), nullable=False)
    
    category = Column(String(100), nullable=False)  # fuel, food, gear, subscriptions, etc.
    business_allowed = Column(Boolean, nullable=False, server_default="1")
    personal_allowed = Column(Boolean, nullable=False, server_default="0")
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    card = relationship("CreditCardProfile", back_populates="spending_rules")


class SpendingTransaction(Base):
    """
    Transaction record with spending rule compliance tracking.
    Flags mismatches for user review - does not auto-classify.
    """
    __tablename__ = "spending_transactions"

    id = Column(Integer, primary_key=True)
    transaction_id = Column(String(255), unique=True, nullable=False)
    card_id = Column(Integer, ForeignKey("credit_card_profiles.id"), nullable=False)
    
    date = Column(DateTime, nullable=False)
    merchant = Column(String(255), nullable=True)
    amount = Column(Integer, nullable=False)  # in cents
    
    detected_category = Column(String(100), nullable=True)  # system detected
    user_classification = Column(String(50), nullable=True)  # business, personal, mixed
    
    rule_compliant = Column(Boolean, nullable=False, server_default="1")
    flagged = Column(Boolean, nullable=False, server_default="0")
    flag_reason = Column(String(255), nullable=True)  # why flagged
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    card = relationship("CreditCardProfile", back_populates="transactions")


class MonthlySpendingSummary(Base):
    """
    Monthly spending summary for review and categorization.
    Organizes data by your rules - not tax determination.
    """
    __tablename__ = "monthly_spending_summaries"

    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("credit_card_profiles.id"), nullable=False)
    
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    
    total_business = Column(Integer, nullable=False, server_default="0")  # cents
    total_personal = Column(Integer, nullable=False, server_default="0")  # cents
    total_flagged = Column(Integer, nullable=False, server_default="0")  # cents
    
    flagged_transactions = Column(JSON, nullable=True)  # list of transaction summaries
    category_breakdown = Column(JSON, nullable=True)  # {category: amount}
    unusual_items = Column(JSON, nullable=True)  # transactions requiring review
    
    subscription_list = Column(JSON, nullable=True)  # recurring transactions
    
    review_notes = Column(Text, nullable=True)  # user review notes
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
