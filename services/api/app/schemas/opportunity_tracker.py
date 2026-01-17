"""
PACK SK: Arbitrage / Side-Hustle Opportunity Tracker
Pydantic schemas for opportunity tracking
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class OpportunitySchema(BaseModel):
    opportunity_id: str = Field(..., description="Unique opportunity identifier")
    name: str = Field(..., description="Opportunity name")
    category: str = Field(..., description="service, product, digital, gig, seasonal, or arbitrage")
    description: Optional[str] = None
    startup_cost: int = Field(..., description="Startup cost in cents")
    expected_effort: Optional[float] = Field(None, description="Hours per week estimate")
    potential_return: Optional[int] = Field(None, description="Expected return in cents")
    risk_level: Optional[str] = Field(None, description="User-defined risk level")
    status: str = Field("idea", description="Current status")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class OpportunityScoreSchema(BaseModel):
    score_id: str = Field(..., description="Unique score identifier")
    opportunity_id: int
    time_efficiency: Optional[float] = Field(None, description="0-10 user score")
    scalability: Optional[float] = Field(None, description="0-10 user score")
    difficulty: Optional[float] = Field(None, description="0-10 user score (lower=easier)")
    personal_interest: Optional[float] = Field(None, description="0-10 user score")
    overall_score: Optional[float] = Field(None, description="User-calculated overall")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class OpportunityPerformanceSchema(BaseModel):
    log_id: str = Field(..., description="Unique log identifier")
    opportunity_id: int
    date: datetime
    effort_hours: Optional[float] = None
    revenue: Optional[int] = Field(None, description="Revenue in cents")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class OpportunitySummarySchema(BaseModel):
    summary_id: str = Field(..., description="Unique summary identifier")
    opportunity_id: int
    period: str = Field(..., description="YYYY-MM format")
    total_effort_hours: float
    total_revenue: int = Field(..., description="Total revenue in cents")
    roi: Optional[float] = Field(None, description="ROI percentage")
    status_update: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class OpportunityComparisonResponse(BaseModel):
    opportunity_name: str
    status: str
    overall_score: Optional[float]
    total_revenue_ytd: int
    total_effort_hours_ytd: float
    hours_per_dollar: Optional[float]
