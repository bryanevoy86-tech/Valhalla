"""PACK 69: Code Compliance Router
API endpoints for compliance checking.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.db import get_db
from app.schemas.code_compliance import ComplianceCheckOut
from app.services.code_compliance_service import run_compliance_check, list_checks

router = APIRouter(prefix="/compliance", tags=["Code Compliance"])


@router.post("/", response_model=ComplianceCheckOut)
def check_blueprint(
    blueprint_id: int,
    region_code: str,
    violations: Optional[str] = None,
    passed: str = "pending",
    db: Session = Depends(get_db)
):
    """Run a compliance check on a blueprint."""
    return run_compliance_check(db, blueprint_id, region_code, violations, passed)


@router.get("/", response_model=list[ComplianceCheckOut])
def get_checks(blueprint_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get compliance checks, optionally filtered by blueprint ID."""
    return list_checks(db, blueprint_id)
