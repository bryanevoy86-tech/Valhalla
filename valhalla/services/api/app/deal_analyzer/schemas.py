"""
Pydantic schemas for Deal Analyzer.
"""
from pydantic import BaseModel, Field
from datetime import datetime


class DealAnalysisCreate(BaseModel):
    property_address: str = Field(..., min_length=1, max_length=300)
    purchase_price: float = Field(..., gt=0, description="Property purchase price")
    rehab_cost: float = Field(..., ge=0, description="Estimated rehab/renovation cost")
    arv: float = Field(..., gt=0, description="After Repair Value")


class DealAnalysisOut(BaseModel):
    id: int
    property_address: str
    purchase_price: float
    rehab_cost: float
    arv: float
    expected_profit: float
    roi: float
    cash_on_cash_return: float | None
    is_profitable: bool
    risk_score: float | None
    ai_recommendation: str
    analysis_notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DealMetrics(BaseModel):
    """Calculated deal metrics for analysis."""
    total_investment: float
    expected_profit: float
    roi_percentage: float
    cash_on_cash_return: float | None
    profit_margin: float
    is_profitable: bool
    risk_score: float
    recommendation: str
