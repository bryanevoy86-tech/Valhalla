"""Schemas for PACK SD: Credit Card & Spending Framework"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CreditCardProfileSchema(BaseModel):
    """Credit card profile schema"""
    card_id: str = Field(..., description="Unique card identifier")
    nickname: str = Field(..., description="User-friendly card name")
    issuer: Optional[str] = Field(None, description="Card issuer")
    card_type: str = Field(..., description="Card type: business, personal, travel, etc.")
    status: str = Field("active", description="active or closed")
    allowed_categories: Optional[list] = Field(None, description="Categories allowed on this card")
    restricted_categories: Optional[list] = Field(None, description="Categories not allowed on this card")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        from_attributes = True


class SpendingRuleSchema(BaseModel):
    """Spending rule for categorizing purchases"""
    rule_id: str = Field(..., description="Unique rule identifier")
    card_id: int = Field(..., description="Card profile ID")
    category: str = Field(..., description="Category: fuel, food, gear, subscriptions, etc.")
    business_allowed: bool = Field(True, description="Is business use allowed for this category")
    personal_allowed: bool = Field(False, description="Is personal use allowed for this category")
    notes: Optional[str] = Field(None, description="Rule notes")
    
    class Config:
        from_attributes = True


class SpendingTransactionSchema(BaseModel):
    """Spending transaction record"""
    transaction_id: str = Field(..., description="Unique transaction ID")
    card_id: int = Field(..., description="Card profile ID")
    date: datetime = Field(..., description="Transaction date")
    merchant: Optional[str] = Field(None, description="Merchant name")
    amount: int = Field(..., description="Amount in cents")
    detected_category: Optional[str] = Field(None, description="System-detected category")
    user_classification: Optional[str] = Field(None, description="business, personal, or mixed")
    rule_compliant: bool = Field(True, description="Is transaction compliant with rules")
    flagged: bool = Field(False, description="Is transaction flagged for review")
    flag_reason: Optional[str] = Field(None, description="Reason for flag")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        from_attributes = True


class MonthlySummarySchema(BaseModel):
    """Monthly spending summary"""
    card_id: int = Field(..., description="Card profile ID")
    year: int = Field(..., description="Year")
    month: int = Field(..., description="Month (1-12)")
    total_business: int = Field(0, description="Total business spending in cents")
    total_personal: int = Field(0, description="Total personal spending in cents")
    total_flagged: int = Field(0, description="Total flagged spending in cents")
    flagged_transactions: Optional[list] = Field(None, description="Flagged transactions")
    category_breakdown: Optional[dict] = Field(None, description="Breakdown by category")
    unusual_items: Optional[list] = Field(None, description="Items requiring review")
    subscription_list: Optional[list] = Field(None, description="Recurring transactions")
    review_notes: Optional[str] = Field(None, description="User review notes")
    
    class Config:
        from_attributes = True


class SpendingStatusResponse(BaseModel):
    """Spending status with compliance check"""
    card_id: int
    month: str
    total_transactions: int
    compliant_count: int
    flagged_count: int
    compliance_percentage: float
    flagged_amount_cents: int
    categories: dict
    requires_review: bool
