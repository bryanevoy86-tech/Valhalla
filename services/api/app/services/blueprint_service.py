"""PACK 68: Blueprint Generator Service
Service layer for blueprint operations.
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.models.blueprint import Blueprint


def create_blueprint(
    db: Session,
    project_name: str,
    property_address: Optional[str],
    specs_payload: str
) -> Blueprint:
    """Create a new blueprint."""
    bp = Blueprint(
        project_name=project_name,
        property_address=property_address,
        specs_payload=specs_payload,
        status="generated"
    )
    db.add(bp)
    db.commit()
    db.refresh(bp)
    return bp


def list_blueprints(db: Session) -> list:
    """List all blueprints in reverse chronological order."""
    return db.query(Blueprint).order_by(Blueprint.id.desc()).all()
