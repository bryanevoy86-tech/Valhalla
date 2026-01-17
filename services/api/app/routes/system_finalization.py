"""PACK 60: System Finalization Router
API endpoints for system finalization and integrity sealing.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.system_finalization_service import create_integrity_seal, deactivate_previous_seals
from app.schemas.system_finalization import SystemIntegritySealOut

router = APIRouter(prefix="/system-finalization", tags=["System Finalization"])


@router.post("/seal", response_model=SystemIntegritySealOut)
def write_seal(schema_version: str, db: Session = Depends(get_db)):
    """Write a new system integrity seal and deactivate previous ones."""
    deactivate_previous_seals(db)
    return create_integrity_seal(db, schema_version)
