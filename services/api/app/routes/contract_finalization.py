"""PACK 64: Contract Engine Finalization Router
API endpoints for contract template and record management.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.contract_finalization_service import (
    create_template, list_templates, generate_contract_record, update_contract_pdf
)
from app.schemas.contract_finalization import (
    ContractTemplateOut, ContractRecordOut
)

router = APIRouter(prefix="/contracts", tags=["Contract Engine"])


@router.post("/templates", response_model=ContractTemplateOut)
def new_template(name: str, version: str, body: str, db: Session = Depends(get_db)):
    """Create a new contract template."""
    return create_template(db, name, version, body)


@router.get("/templates", response_model=list[ContractTemplateOut])
def fetch_templates(db: Session = Depends(get_db)):
    """Fetch all active contract templates."""
    return list_templates(db)


@router.post("/records", response_model=ContractRecordOut)
def new_contract(template_id: int, filled_fields: str, db: Session = Depends(get_db)):
    """Generate a new contract record from a template."""
    return generate_contract_record(db, template_id, filled_fields)


@router.post("/records/{record_id}/pdf", response_model=ContractRecordOut)
def set_output_pdf(record_id: int, pdf_path: str, db: Session = Depends(get_db)):
    """Set output PDF path for a contract record."""
    return update_contract_pdf(db, record_id, pdf_path)
