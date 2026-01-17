# services/api/app/routers/contracts_lifecycle.py

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.contract_record import (
    ContractCreate,
    ContractUpdateStatus,
    ContractOut,
)
from app.services.contract_lifecycle import (
    create_contract,
    update_contract_status,
    get_contract,
    list_contracts_for_deal,
    list_contracts_by_status,
    archive_contract,
)

router = APIRouter(
    prefix="/contracts/lifecycle",
    tags=["Contracts", "Lifecycle"]
)


@router.post("/", response_model=ContractOut, status_code=status.HTTP_201_CREATED)
def create_contract_endpoint(payload: ContractCreate, db: Session = Depends(get_db)):
    """Create a new contract record in draft status."""
    obj = create_contract(db, payload)
    return obj


@router.patch("/{contract_id}/status", response_model=ContractOut)
def update_status_endpoint(
    contract_id: int,
    payload: ContractUpdateStatus,
    db: Session = Depends(get_db)
):
    """Update contract status (draft -> under_review -> approved -> sent -> signed -> archived)."""
    obj = update_contract_status(db, contract_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Contract not found")
    return obj


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract_endpoint(contract_id: int, db: Session = Depends(get_db)):
    """Get a specific contract by ID."""
    obj = get_contract(db, contract_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Contract not found")
    return obj


@router.get("/by-deal/{deal_id}", response_model=List[ContractOut])
def list_for_deal_endpoint(deal_id: int, db: Session = Depends(get_db)):
    """Get all contracts for a specific deal."""
    return list_contracts_for_deal(db, deal_id)


@router.get("/by-status/", response_model=List[ContractOut])
def list_by_status_endpoint(
    status: str = Query(..., description="Filter by status: draft, under_review, approved, sent, signed, archived"),
    db: Session = Depends(get_db)
):
    """Get all contracts with a specific status."""
    return list_contracts_by_status(db, status)


@router.post("/{contract_id}/archive", response_model=ContractOut)
def archive_contract_endpoint(contract_id: int, db: Session = Depends(get_db)):
    """Archive a contract (convenience endpoint)."""
    obj = archive_contract(db, contract_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Contract not found")
    return obj
