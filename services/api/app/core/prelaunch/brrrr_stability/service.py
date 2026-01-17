"""PACK-PRELAUNCH-12: BRRRR Stability Engine Service"""
from typing import List
from sqlalchemy.orm import Session
from . import models


def list_stability(db: Session) -> List[models.BRRRRStability]:
    """List all BRRRR property stability records, newest first."""
    return db.query(models.BRRRRStability).order_by(models.BRRRRStability.updated_at.desc()).all()


def get_stability(db: Session, property_address: str) -> models.BRRRRStability | None:
    """Get stability record for a specific property."""
    return db.query(models.BRRRRStability).filter(
        models.BRRRRStability.property_address == property_address
    ).first()
