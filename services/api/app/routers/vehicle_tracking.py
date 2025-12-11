"""Router for PACK SE: Vehicle Use & Expense Categorization Framework"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.schemas.vehicle_tracking import (
    VehicleProfileSchema, VehicleTripLogSchema, VehicleExpenseSchema,
    MileageSummarySchema, VehicleStatusResponse
)
from app.services import vehicle_tracking

router = APIRouter(prefix="/vehicles", tags=["PACK SE: Vehicle Tracking"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ========== VEHICLE PROFILE ENDPOINTS ==========

@router.post("/profiles", response_model=VehicleProfileSchema)
def create_vehicle_profile(profile: VehicleProfileSchema, db: Session = Depends(get_db)):
    """Create new vehicle profile"""
    return vehicle_tracking.create_vehicle_profile(db, profile)


@router.get("/profiles", response_model=list[VehicleProfileSchema])
def list_vehicle_profiles(db: Session = Depends(get_db)):
    """List all vehicle profiles"""
    return vehicle_tracking.list_vehicle_profiles(db)


@router.get("/profiles/{vehicle_id}", response_model=VehicleProfileSchema)
def get_vehicle_profile(vehicle_id: int, db: Session = Depends(get_db)):
    """Get vehicle profile details"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    return vehicle


@router.patch("/profiles/{vehicle_id}", response_model=VehicleProfileSchema)
def update_vehicle_profile(vehicle_id: int, profile: VehicleProfileSchema, db: Session = Depends(get_db)):
    """Update vehicle profile"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    
    return vehicle_tracking.update_vehicle_profile(db, vehicle_id, profile)


# ========== TRIP LOG ENDPOINTS ==========

@router.post("/trips", response_model=VehicleTripLogSchema)
def create_trip_log(trip: VehicleTripLogSchema, db: Session = Depends(get_db)):
    """Create trip log entry"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, trip.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    
    return vehicle_tracking.create_trip_log(db, trip)


@router.get("/trips/{vehicle_id}", response_model=list[VehicleTripLogSchema])
def get_vehicle_trips(vehicle_id: int, db: Session = Depends(get_db)):
    """Get all trips for vehicle"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    
    return vehicle_tracking.get_vehicle_trips(db, vehicle_id)


# ========== VEHICLE EXPENSE ENDPOINTS ==========

@router.post("/expenses", response_model=VehicleExpenseSchema)
def create_vehicle_expense(expense: VehicleExpenseSchema, db: Session = Depends(get_db)):
    """Create vehicle expense entry"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, expense.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    
    return vehicle_tracking.create_vehicle_expense(db, expense)


@router.get("/expenses/{vehicle_id}", response_model=list[VehicleExpenseSchema])
def get_vehicle_expenses(vehicle_id: int, db: Session = Depends(get_db)):
    """Get all expenses for vehicle"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    
    return vehicle_tracking.get_vehicle_expenses(db, vehicle_id)


@router.get("/expenses/{vehicle_id}/category/{category}", response_model=list[VehicleExpenseSchema])
def get_expenses_by_category(vehicle_id: int, category: str, db: Session = Depends(get_db)):
    """Get expenses by category"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    
    return vehicle_tracking.get_expenses_by_category(db, vehicle_id, category)


# ========== MILEAGE SUMMARY ENDPOINTS ==========

@router.post("/mileage/{vehicle_id}/{year}/{month}", response_model=MileageSummarySchema)
def generate_mileage_summary(vehicle_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """Generate monthly mileage summary"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    
    return vehicle_tracking.generate_mileage_summary(db, vehicle_id, year, month)


@router.get("/mileage/{vehicle_id}/{year}", response_model=MileageSummarySchema)
def get_annual_mileage(vehicle_id: int, year: int, db: Session = Depends(get_db)):
    """Get annual mileage summary"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    
    return vehicle_tracking.generate_mileage_summary(db, vehicle_id, year, None)


@router.get("/status/{vehicle_id}/{year}/{month}", response_model=VehicleStatusResponse)
def get_vehicle_status(vehicle_id: int, year: int, month: int, db: Session = Depends(get_db)):
    """Get vehicle status summary"""
    vehicle = vehicle_tracking.get_vehicle_profile(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle profile not found")
    
    summary = vehicle_tracking.get_vehicle_summary(db, vehicle_id, year, month)
    
    return VehicleStatusResponse(
        vehicle_id=vehicle_id,
        name=vehicle.name,
        period=f"{year}-{month:02d}",
        total_kms=summary["mileage_summary"].total_kms,
        business_kms=summary["mileage_summary"].business_kms,
        personal_kms=summary["mileage_summary"].personal_kms,
        business_percentage=summary["mileage_summary"].business_percentage or 0,
        trip_count=summary["mileage_summary"].trip_count,
        last_trip_date=summary["recent_trips"][0].date if summary["recent_trips"] else None,
        recent_expenses=[{"date": e.date, "category": e.category, "amount": e.amount} for e in summary["recent_trips"][:5]]
    )
