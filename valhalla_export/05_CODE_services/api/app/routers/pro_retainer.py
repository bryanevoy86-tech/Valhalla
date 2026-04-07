# services/api/app/routers/pro_retainer.py

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app.core.db import get_db
from app.models.pro_retainer import Retainer
from app.models.pro_scorecard import Professional
from app.schemas.pro_retainer import RetainerIn, RetainerOut, HoursLogRequest

router = APIRouter(
    prefix="/pros/retainers",
    tags=["Professionals", "Retainers"]
)


@router.post("/", response_model=RetainerOut, status_code=status.HTTP_201_CREATED)
def create_retainer(payload: RetainerIn, db: Session = Depends(get_db)):
    """Create a new retainer agreement with a professional."""
    # Verify professional exists
    pro = db.query(Professional).filter(Professional.id == payload.professional_id).first()
    if not pro:
        raise HTTPException(404, "Professional not found")
    
    ret = Retainer(**payload.dict())
    db.add(ret)
    db.commit()
    db.refresh(ret)
    return ret


@router.get("/{retainer_id}", response_model=RetainerOut)
def get_retainer(retainer_id: int, db: Session = Depends(get_db)):
    """Get retainer details."""
    ret = db.query(Retainer).filter(Retainer.id == retainer_id).first()
    if not ret:
        raise HTTPException(404, "Retainer not found")
    return ret


@router.post("/{retainer_id}/log_hours")
def log_hours(retainer_id: int, payload: HoursLogRequest, db: Session = Depends(get_db)):
    """Log hours used against a retainer."""
    ret = db.query(Retainer).filter(Retainer.id == retainer_id).first()
    if not ret:
        raise HTTPException(404, "Retainer not found")
    
    ret.hours_used += payload.hours
    db.commit()
    db.refresh(ret)
    
    # Calculate status
    remaining = ret.monthly_hours_included - ret.hours_used
    overage = max(0, ret.hours_used - ret.monthly_hours_included)
    utilization = (ret.hours_used / ret.monthly_hours_included) * 100
    
    # Check if renewal is approaching (within 7 days)
    days_to_renewal = (ret.renewal_date - date.today()).days
    renewal_warning = days_to_renewal <= 7
    
    # Check if hours are almost consumed (>90%)
    hours_warning = utilization > 90
    
    return {
        "status": "ok",
        "hours_used": ret.hours_used,
        "hours_remaining": remaining,
        "overage_hours": overage,
        "utilization_pct": round(utilization, 1),
        "warnings": {
            "renewal_approaching": renewal_warning,
            "days_to_renewal": days_to_renewal,
            "hours_nearly_consumed": hours_warning,
        }
    }


@router.get("/professional/{professional_id}", response_model=list[RetainerOut])
def list_professional_retainers(professional_id: int, db: Session = Depends(get_db)):
    """Get all retainers for a specific professional."""
    retainers = db.query(Retainer).filter(
        Retainer.professional_id == professional_id
    ).all()
    return retainers


@router.patch("/{retainer_id}/deactivate")
def deactivate_retainer(retainer_id: int, db: Session = Depends(get_db)):
    """Deactivate a retainer agreement."""
    ret = db.query(Retainer).filter(Retainer.id == retainer_id).first()
    if not ret:
        raise HTTPException(404, "Retainer not found")
    
    ret.is_active = False
    db.commit()
    return {"status": "deactivated", "retainer_id": retainer_id}
