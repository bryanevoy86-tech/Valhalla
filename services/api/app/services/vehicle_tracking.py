"""Services for PACK SE: Vehicle Use & Expense Categorization Framework"""

from sqlalchemy.orm import Session
from app.models.vehicle_tracking import (
    VehicleProfile, VehicleTripLog, VehicleExpense, MileageSummary
)
from app.schemas.vehicle_tracking import (
    VehicleProfileSchema, VehicleTripLogSchema, VehicleExpenseSchema, MileageSummarySchema
)
from datetime import datetime
from typing import List, Optional


# ========== VEHICLE PROFILE FUNCTIONS ==========

def create_vehicle_profile(db: Session, vehicle_data: VehicleProfileSchema) -> VehicleProfile:
    """Create new vehicle profile"""
    db_vehicle = VehicleProfile(**vehicle_data.model_dump())
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    return db_vehicle


def get_vehicle_profile(db: Session, vehicle_id: int) -> Optional[VehicleProfile]:
    """Get vehicle profile by ID"""
    return db.query(VehicleProfile).filter(VehicleProfile.id == vehicle_id).first()


def list_vehicle_profiles(db: Session) -> List[VehicleProfile]:
    """List all vehicle profiles"""
    return db.query(VehicleProfile).all()


def update_vehicle_profile(db: Session, vehicle_id: int, vehicle_data: VehicleProfileSchema) -> VehicleProfile:
    """Update vehicle profile"""
    db_vehicle = get_vehicle_profile(db, vehicle_id)
    if db_vehicle:
        for key, value in vehicle_data.model_dump(exclude_unset=True).items():
            setattr(db_vehicle, key, value)
        db_vehicle.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_vehicle)
    return db_vehicle


# ========== TRIP LOG FUNCTIONS ==========

def create_trip_log(db: Session, trip_data: VehicleTripLogSchema) -> VehicleTripLog:
    """Create trip log entry"""
    db_trip = VehicleTripLog(**trip_data.model_dump())
    db.add(db_trip)
    db.commit()
    db.refresh(db_trip)
    return db_trip


def get_trip_log(db: Session, trip_id: int) -> Optional[VehicleTripLog]:
    """Get trip log by ID"""
    return db.query(VehicleTripLog).filter(VehicleTripLog.id == trip_id).first()


def get_vehicle_trips(db: Session, vehicle_id: int) -> List[VehicleTripLog]:
    """Get all trips for a vehicle"""
    return db.query(VehicleTripLog).filter(VehicleTripLog.vehicle_id == vehicle_id).all()


def get_trips_by_date_range(db: Session, vehicle_id: int, start_date: datetime, end_date: datetime) -> List[VehicleTripLog]:
    """Get trips within date range"""
    return db.query(VehicleTripLog).filter(
        VehicleTripLog.vehicle_id == vehicle_id,
        VehicleTripLog.date >= start_date,
        VehicleTripLog.date <= end_date
    ).all()


# ========== VEHICLE EXPENSE FUNCTIONS ==========

def create_vehicle_expense(db: Session, expense_data: VehicleExpenseSchema) -> VehicleExpense:
    """Create vehicle expense entry"""
    db_expense = VehicleExpense(**expense_data.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


def get_vehicle_expenses(db: Session, vehicle_id: int) -> List[VehicleExpense]:
    """Get all expenses for a vehicle"""
    return db.query(VehicleExpense).filter(VehicleExpense.vehicle_id == vehicle_id).all()


def get_expenses_by_category(db: Session, vehicle_id: int, category: str) -> List[VehicleExpense]:
    """Get expenses by category"""
    return db.query(VehicleExpense).filter(
        VehicleExpense.vehicle_id == vehicle_id,
        VehicleExpense.category == category
    ).all()


def calculate_business_expenses(db: Session, vehicle_id: int) -> float:
    """Calculate total business-related expenses"""
    expenses = get_vehicle_expenses(db, vehicle_id)
    total = 0
    for exp in expenses:
        if exp.business_related:
            if exp.business_percentage:
                total += exp.amount * (exp.business_percentage / 100)
            else:
                total += exp.amount
    return total


# ========== MILEAGE SUMMARY FUNCTIONS ==========

def generate_mileage_summary(
    db: Session,
    vehicle_id: int,
    year: int,
    month: Optional[int] = None
) -> MileageSummary:
    """
    Generate mileage summary for vehicle.
    If month is None, generates annual summary.
    """
    # Get trips for period
    if month:
        trips = db.query(VehicleTripLog).filter(
            VehicleTripLog.vehicle_id == vehicle_id,
            VehicleTripLog.date.op('year')() == year,
            VehicleTripLog.date.op('month')() == month
        ).all()
        period = f"{year}-{month:02d}"
    else:
        trips = db.query(VehicleTripLog).filter(
            VehicleTripLog.vehicle_id == vehicle_id,
            VehicleTripLog.date.op('year')() == year
        ).all()
        period = str(year)
    
    # Calculate totals
    total_kms = sum(t.kms for t in trips)
    business_kms = sum(t.business_kms or t.kms for t in trips if t.business_use)
    personal_kms = sum(t.personal_kms or t.kms for t in trips if t.personal_use)
    mixed_kms = sum(t.kms for t in trips if t.mixed_use)
    
    business_percentage = (business_kms / total_kms * 100) if total_kms > 0 else 0
    
    # Detect repetitive routes
    route_map = {}
    for trip in trips:
        route_key = f"{trip.start_location}->{trip.end_location}"
        if route_key not in route_map:
            route_map[route_key] = []
        route_map[route_key].append(trip)
    
    repetitive_routes = [
        {
            "route": route,
            "count": len(trips_list),
            "avg_kms": sum(t.kms for t in trips_list) / len(trips_list)
        }
        for route, trips_list in route_map.items()
        if len(trips_list) > 1
    ]
    
    # Detect unusual days (high mileage)
    avg_kms = total_kms / len(trips) if trips else 0
    unusual_days = [
        {
            "date": trip.date.isoformat(),
            "kms": trip.kms,
            "purpose": trip.purpose
        }
        for trip in trips
        if trip.kms > avg_kms * 2  # Over 2x average
    ]
    
    # Create or update summary
    summary = db.query(MileageSummary).filter(
        MileageSummary.vehicle_id == vehicle_id,
        MileageSummary.year == year,
        MileageSummary.month == month
    ).first()
    
    if summary:
        summary.total_kms = total_kms
        summary.business_kms = business_kms
        summary.personal_kms = personal_kms
        summary.mixed_kms = mixed_kms
        summary.business_percentage = business_percentage
        summary.trip_count = len(trips)
        summary.repetitive_routes = repetitive_routes
        summary.unusual_days = unusual_days
        summary.updated_at = datetime.utcnow()
    else:
        summary = MileageSummary(
            vehicle_id=vehicle_id,
            period=period,
            year=year,
            month=month,
            total_kms=total_kms,
            business_kms=business_kms,
            personal_kms=personal_kms,
            mixed_kms=mixed_kms,
            business_percentage=business_percentage,
            trip_count=len(trips),
            repetitive_routes=repetitive_routes,
            unusual_days=unusual_days
        )
        db.add(summary)
    
    db.commit()
    db.refresh(summary)
    return summary


def get_mileage_summary(
    db: Session,
    vehicle_id: int,
    year: int,
    month: Optional[int] = None
) -> Optional[MileageSummary]:
    """Get existing mileage summary"""
    return db.query(MileageSummary).filter(
        MileageSummary.vehicle_id == vehicle_id,
        MileageSummary.year == year,
        MileageSummary.month == month
    ).first()


def get_vehicle_summary(db: Session, vehicle_id: int, year: int, month: Optional[int] = None) -> dict:
    """Get complete vehicle summary for period"""
    vehicle = get_vehicle_profile(db, vehicle_id)
    mileage = generate_mileage_summary(db, vehicle_id, year, month)
    expenses = get_vehicle_expenses(db, vehicle_id)
    business_expenses = calculate_business_expenses(db, vehicle_id)
    
    return {
        "vehicle": vehicle,
        "mileage_summary": mileage,
        "total_expenses": sum(e.amount for e in expenses),
        "business_expenses": business_expenses,
        "recent_trips": get_vehicle_trips(db, vehicle_id)[-10:]  # Last 10 trips
    }
