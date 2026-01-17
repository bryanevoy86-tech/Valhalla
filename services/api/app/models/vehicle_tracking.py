"""
PACK SE: Vehicle Use & Expense Categorization Framework
Neutral logging engine for vehicle trips and expenses.
Does not provide tax eligibility judgement - only records data.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.db import Base


class VehicleProfile(Base):
    """
    Vehicle profile with user-defined ownership and type.
    Neutral storage - no assumptions about business use.
    """
    __tablename__ = "vehicle_profiles"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)  # "Urus", "F150", "Model 3"
    type = Column(String(100), nullable=False)  # user-defined categories
    
    ownership = Column(String(100), nullable=False)  # company-owned, personally-owned, leased
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    vin = Column(String(100), nullable=True)
    
    status = Column(String(50), nullable=False, server_default="active")
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    trip_logs = relationship("VehicleTripLog", back_populates="vehicle")
    expenses = relationship("VehicleExpense", back_populates="vehicle")


class VehicleTripLog(Base):
    """
    Trip log in CRA-compliant format: date, location, km, purpose.
    100% recordkeeping - no tax determinations.
    """
    __tablename__ = "vehicle_trip_logs"

    id = Column(Integer, primary_key=True)
    trip_id = Column(String(255), unique=True, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicle_profiles.id"), nullable=False)
    
    date = Column(DateTime, nullable=False)
    start_location = Column(String(255), nullable=True)
    end_location = Column(String(255), nullable=True)
    
    kms = Column(Float, nullable=False)
    purpose = Column(String(255), nullable=True)  # client meeting, viewing, pickup, etc.
    
    # User-provided classification - no auto-determination
    business_use = Column(Boolean, nullable=False, server_default="0")
    personal_use = Column(Boolean, nullable=False, server_default="0")
    mixed_use = Column(Boolean, nullable=False, server_default="0")
    
    business_kms = Column(Float, nullable=True)  # user-calculated
    personal_kms = Column(Float, nullable=True)  # user-calculated
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    vehicle = relationship("VehicleProfile", back_populates="trip_logs")


class VehicleExpense(Base):
    """
    Vehicle expense with user-defined business/personal split.
    Neutral categorization - user provides classification.
    """
    __tablename__ = "vehicle_expenses"

    id = Column(Integer, primary_key=True)
    expense_id = Column(String(255), unique=True, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicle_profiles.id"), nullable=False)
    
    date = Column(DateTime, nullable=False)
    category = Column(String(100), nullable=False)  # fuel, maintenance, insurance, wrap, detailing, tires
    amount = Column(Float, nullable=False)
    
    # User-provided classification
    business_related = Column(Boolean, nullable=False, server_default='false')
    business_percentage = Column(Float, nullable=True)  # 0-100 for split expenses
    
    description = Column(String(255), nullable=True)
    receipt_url = Column(String(255), nullable=True)
    
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    vehicle = relationship("VehicleProfile", back_populates="expenses")


class MileageSummary(Base):
    """
    Monthly/annual mileage summary organized by your categories.
    Pure data organization - no tax implications.
    """
    __tablename__ = "mileage_summaries"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicle_profiles.id"), nullable=False)
    
    period = Column(String(50), nullable=False)  # "2025-01" for January 2025
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=True)  # 1-12, NULL for annual
    
    total_kms = Column(Float, nullable=False, server_default="0")
    business_kms = Column(Float, nullable=False, server_default="0")
    personal_kms = Column(Float, nullable=False, server_default="0")
    mixed_kms = Column(Float, nullable=False, server_default="0")
    
    business_percentage = Column(Float, nullable=True)  # calculated
    trip_count = Column(Integer, nullable=False, server_default="0")
    
    # Repeating routes detected
    repetitive_routes = Column(JSON, nullable=True)  # [{route, count, avg_kms}]
    
    unusual_days = Column(JSON, nullable=True)  # high-mileage days for review
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now())
