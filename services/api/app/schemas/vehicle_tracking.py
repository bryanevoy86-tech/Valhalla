"""Schemas for PACK SE: Vehicle Use & Expense Categorization Framework"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VehicleProfileSchema(BaseModel):
    """Vehicle profile schema"""
    vehicle_id: str = Field(..., description="Unique vehicle identifier")
    name: str = Field(..., description="Vehicle nickname (Urus, F150, etc.)")
    type: str = Field(..., description="Vehicle type (user-defined)")
    ownership: str = Field(..., description="company-owned, personally-owned, leased")
    make: Optional[str] = Field(None, description="Vehicle make")
    model: Optional[str] = Field(None, description="Vehicle model")
    year: Optional[int] = Field(None, description="Vehicle year")
    vin: Optional[str] = Field(None, description="VIN")
    status: str = Field("active", description="active or inactive")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        from_attributes = True


class VehicleTripLogSchema(BaseModel):
    """Trip log schema - CRA-safe format"""
    trip_id: str = Field(..., description="Unique trip identifier")
    vehicle_id: int = Field(..., description="Vehicle profile ID")
    date: datetime = Field(..., description="Trip date")
    start_location: Optional[str] = Field(None, description="Starting location")
    end_location: Optional[str] = Field(None, description="Ending location")
    kms: float = Field(..., description="Total kilometers")
    purpose: Optional[str] = Field(None, description="Trip purpose")
    business_use: bool = Field(False, description="Is this business use")
    personal_use: bool = Field(False, description="Is this personal use")
    mixed_use: bool = Field(False, description="Is this mixed use")
    business_kms: Optional[float] = Field(None, description="Business kilometers (if split)")
    personal_kms: Optional[float] = Field(None, description="Personal kilometers (if split)")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        from_attributes = True


class VehicleExpenseSchema(BaseModel):
    """Vehicle expense schema"""
    expense_id: str = Field(..., description="Unique expense identifier")
    vehicle_id: int = Field(..., description="Vehicle profile ID")
    date: datetime = Field(..., description="Expense date")
    category: str = Field(..., description="fuel, maintenance, insurance, wrap, detailing, tires")
    amount: float = Field(..., description="Expense amount")
    business_related: bool = Field(False, description="Is this business-related")
    business_percentage: Optional[float] = Field(None, description="Business use percentage (0-100)")
    description: Optional[str] = Field(None, description="Expense description")
    receipt_url: Optional[str] = Field(None, description="Receipt file path")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    class Config:
        from_attributes = True


class MileageSummarySchema(BaseModel):
    """Mileage summary schema"""
    vehicle_id: int = Field(..., description="Vehicle profile ID")
    period: str = Field(..., description="Period (YYYY-MM or YYYY)")
    year: int = Field(..., description="Year")
    month: Optional[int] = Field(None, description="Month (1-12)")
    total_kms: float = Field(0, description="Total kilometers")
    business_kms: float = Field(0, description="Business kilometers")
    personal_kms: float = Field(0, description="Personal kilometers")
    mixed_kms: float = Field(0, description="Mixed-use kilometers")
    business_percentage: Optional[float] = Field(None, description="Business use percentage")
    trip_count: int = Field(0, description="Number of trips")
    repetitive_routes: Optional[list] = Field(None, description="Repeating routes detected")
    unusual_days: Optional[list] = Field(None, description="High-mileage days")
    
    class Config:
        from_attributes = True


class VehicleStatusResponse(BaseModel):
    """Vehicle status summary"""
    vehicle_id: int
    name: str
    period: str
    total_kms: float
    business_kms: float
    personal_kms: float
    business_percentage: float
    trip_count: int
    last_trip_date: Optional[datetime]
    recent_expenses: list
