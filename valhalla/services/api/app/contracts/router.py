"""Contract pipeline REST router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.contracts.service import create_contract, update_contract_state, send_contract
from app.db.base import get_db


router = APIRouter(prefix="/contracts", tags=["contracts"])


class ContractCreateRequest(BaseModel):
    template_id: int
    title: str
    merge_data: dict
    deal_id: str = None


class ContractStateUpdateRequest(BaseModel):
    new_state: str
    actor: str = None


@router.post("/create")
def create_contract_endpoint(
    payload: ContractCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new contract from a template."""
    try:
        contract = create_contract(
            db=db,
            template_id=payload.template_id,
            title=payload.title,
            merge_data=payload.merge_data,
            deal_id=payload.deal_id
        )
        return {
            "id": contract.id,
            "state": contract.state,
            "template_id": contract.template_id,
            "created_at": contract.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contract_id}/state")
def update_state_endpoint(
    contract_id: str,
    payload: ContractStateUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update contract state."""
    try:
        contract = update_contract_state(
            db=db,
            contract_id=contract_id,
            new_state=payload.new_state,
            actor=payload.actor
        )
        return {
            "id": contract.id,
            "state": contract.state,
            "updated_at": contract.updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contract_id}/send")
def send_contract_endpoint(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Send contract for signing (requires LIVE mode)."""
    try:
        contract = send_contract(db=db, contract_id=contract_id)
        return {
            "id": contract.id,
            "state": contract.state,
            "message": "Contract sent for signature"
        }
    except RuntimeError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{contract_id}")
def get_contract_endpoint(
    contract_id: str,
    db: Session = Depends(get_db)
):
    """Get contract details."""
    from app.contracts.models import Contract
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return {
        "id": contract.id,
        "title": contract.title,
        "state": contract.state,
        "template_id": contract.template_id,
        "deal_id": contract.deal_id,
        "created_at": contract.created_at.isoformat(),
        "updated_at": contract.updated_at.isoformat()
    }
