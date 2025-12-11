"""
PACK SH: Multi-Year Projection Snapshot Framework
Pydantic schemas for projection scenarios and variance tracking
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AssumptionSet(BaseModel):
    income_growth_rate: Optional[float] = Field(None, description="Annual income growth %")
    expense_growth_rate: Optional[float] = Field(None, description="Annual expense growth %")
    real_estate_acquisitions: Optional[int] = Field(None, description="Number of properties to acquire")
    avg_cashflow_per_property: Optional[int] = Field(None, description="Expected cashflow in cents")
    savings_rate: Optional[float] = Field(None, description="Savings rate %")
    custom: Optional[Dict[str, Any]] = Field(None, description="Any custom assumptions")


class ProjectionScenarioSchema(BaseModel):
    scenario_id: str = Field(..., description="Unique scenario identifier")
    name: str = Field(..., description="Scenario name (e.g., 'Conservative', 'Growth')")
    description: Optional[str] = Field(None, description="Detailed description")
    created_by: Optional[str] = Field(None, description="User or source")
    assumptions: Optional[AssumptionSet] = Field(None, description="User-defined assumptions")

    class Config:
        from_attributes = True


class ProjectionYearSchema(BaseModel):
    scenario_id: int
    year: int = Field(..., description="Calendar year")
    expected_income: int = Field(..., description="Expected income in cents")
    expected_expenses: int = Field(..., description="Expected expenses in cents")
    expected_savings: int = Field(..., description="Expected savings in cents")
    expected_cashflow: int = Field(..., description="Expected cashflow in cents")
    expected_net_worth: int = Field(..., description="Expected net worth in cents")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectionVarianceSchema(BaseModel):
    variance_id: str = Field(..., description="Unique variance identifier")
    scenario_id: int
    year: int = Field(..., description="Calendar year")
    metric: str = Field(..., description="income, expenses, savings, cashflow, or net_worth")
    expected: int = Field(..., description="Expected value in cents")
    actual: int = Field(..., description="Actual value in cents")
    difference: int = Field(..., description="Variance in cents")
    difference_percent: Optional[float] = Field(None, description="Variance as percentage")
    explanation: Optional[str] = Field(None, description="User-provided explanation")

    class Config:
        from_attributes = True


class ProjectionReportSchema(BaseModel):
    report_id: str = Field(..., description="Unique report identifier")
    scenario_id: int
    generated_at: datetime
    summary: Optional[Dict[str, Any]] = Field(None, description="Report summary")
    narrative: Optional[str] = Field(None, description="Family-friendly narrative")
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class ScenarioComparisonResponse(BaseModel):
    scenario_name: str
    years_included: int
    total_expected_income: int
    total_expected_expenses: int
    total_actual_income: Optional[int] = None
    total_actual_expenses: Optional[int] = None
    overall_variance: Optional[int] = None
