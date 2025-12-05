# services/api/app/services/contract_lifecycle.py

from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.contract_record import ContractRecord
from app.schemas.contract_record import ContractCreate, ContractUpdateStatus


def create_contract(db: Session, payload: ContractCreate) -> ContractRecord:
    """Create a new contract record in draft status."""
    obj = ContractRecord(
        deal_id=payload.deal_id,
        title=payload.title,
        professional_id=payload.professional_id,
        storage_url=payload.storage_url,
        status="draft",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_contract_status(
    db: Session,
    contract_id: int,
    payload: ContractUpdateStatus
) -> Optional[ContractRecord]:
    """Update contract status and optionally storage URL."""
    obj = db.query(ContractRecord).filter(ContractRecord.id == contract_id).first()
    if not obj:
        return None

    obj.status = payload.status
    if payload.storage_url is not None:
        obj.storage_url = payload.storage_url

    # Auto-set signed_at timestamp when status becomes signed
    if payload.status == "signed" and obj.signed_at is None:
        obj.signed_at = datetime.utcnow()

    # Bump version for major transitions
    if payload.status in ["under_review", "approved", "signed"]:
        obj.version += 1

    db.commit()
    db.refresh(obj)
    return obj


def get_contract(db: Session, contract_id: int) -> Optional[ContractRecord]:
    """Get a specific contract by ID."""
    return db.query(ContractRecord).filter(ContractRecord.id == contract_id).first()


def list_contracts_for_deal(db: Session, deal_id: int) -> List[ContractRecord]:
    """Get all contracts associated with a deal."""
    return db.query(ContractRecord).filter(ContractRecord.deal_id == deal_id).all()


def list_contracts_by_status(db: Session, status: str) -> List[ContractRecord]:
    """Get all contracts with a specific status."""
    return db.query(ContractRecord).filter(ContractRecord.status == status).all()


def archive_contract(db: Session, contract_id: int) -> Optional[ContractRecord]:
    """Archive a contract (shortcut for status update)."""
    return update_contract_status(
        db,
        contract_id,
        ContractUpdateStatus(status="archived")
    )
