"""PACK 68: Blueprint Generator Router
API endpoints for blueprint generation and retrieval.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.schemas.blueprint import BlueprintOut
from app.services.blueprint_service import create_blueprint, list_blueprints

router = APIRouter(prefix="/blueprint", tags=["Blueprint Engine"])


@router.post("/", response_model=BlueprintOut)
def new_blueprint(
    project_name: str,
    specs_payload: str,
    property_address: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new blueprint."""
    return create_blueprint(db, project_name, property_address, specs_payload)


@router.get("/", response_model=list[BlueprintOut])
def get_blueprints(db: Session = Depends(get_db)):
    """Get all blueprints."""
    return list_blueprints(db)
