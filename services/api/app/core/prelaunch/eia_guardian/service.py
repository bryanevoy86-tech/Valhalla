"""PACK-PRELAUNCH-10: EIA Guardian Engine Service"""
from sqlalchemy.orm import Session
from . import models


def compute_risk(current: float, limit: float) -> str:
    """Compute risk level based on income ratio to limit.
    
    RED: >= 95% of limit
    YELLOW: 75-94% of limit
    GREEN: < 75% of limit
    """
    if limit == 0:
        return "GREEN"
    
    ratio = current / limit
    if ratio >= 0.95:
        return "RED"
    if ratio >= 0.75:
        return "YELLOW"
    return "GREEN"


def get_status(db: Session) -> models.EIAStatus:
    """Get current EIA status, creating default if none exists."""
    status = db.query(models.EIAStatus).first()
    if not status:
        status = models.EIAStatus(
            monthly_limit=1000.0,
            current_income=0.0,
            projected_income=0.0,
            risk_level="GREEN",
            recommendations={"note": "No risk detected yet."},
        )
        db.add(status)
        db.commit()
        db.refresh(status)

    # Recalculate risk level
    status.risk_level = compute_risk(status.current_income, status.monthly_limit)
    db.commit()
    db.refresh(status)
    return status
