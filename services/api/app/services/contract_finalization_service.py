"""PACK 64: Contract Engine Finalization Service
Service layer for contract template and record operations.
"""

from sqlalchemy.orm import Session

from app.models.contracts import ContractTemplate
from app.models.contract_record import ContractRecord


def create_template(db: Session, name: str, version: str, body: str) -> ContractTemplate:
    """Create a new contract template."""
    tpl = ContractTemplate(name=name, version=version, body=body)
    db.add(tpl)
    db.commit()
    db.refresh(tpl)
    return tpl


def list_templates(db: Session) -> list:
    """List all active contract templates."""
    return db.query(ContractTemplate).filter(ContractTemplate.active == True).all()


def generate_contract_record(db: Session, template_id: int, filled_fields: str) -> ContractRecord:
    """Generate a new contract record from a template."""
    record = ContractRecord(
        template_id=template_id,
        filled_fields=filled_fields,
        status="generated"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_contract_pdf(db: Session, record_id: int, pdf_path: str) -> ContractRecord:
    """Update contract record with PDF output path."""
    record = db.query(ContractRecord).filter(ContractRecord.id == record_id).first()
    if record:
        record.output_pdf_path = pdf_path
        db.commit()
        db.refresh(record)
    return record
