"""Contract service - business logic for contract lifecycle."""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.contracts.models import Contract, ContractEvent
from app.core.runtime_flags import is_live


def create_contract(db: Session, template_id: int, title: str, merge_data: dict, deal_id: str = None) -> Contract:
    """Create a new contract from a template."""
    contract = Contract(
        id=f"ctr_{uuid.uuid4().hex[:12]}",
        template_id=template_id,
        title=title,
        merge_data=merge_data,
        deal_id=deal_id,
        state="DRAFT"
    )
    db.add(contract)
    
    # Record creation event
    _log_event(db, contract.id, "created", meta={"template_id": template_id})
    
    db.commit()
    db.refresh(contract)
    return contract


def update_contract_state(db: Session, contract_id: str, new_state: str, actor: str = None) -> Contract:
    """Update contract state and log the change."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError(f"Contract {contract_id} not found")
    
    old_state = contract.state
    contract.state = new_state
    db.add(contract)
    
    _log_event(db, contract_id, "state_changed", actor=actor, meta={
        "old_state": old_state,
        "new_state": new_state
    })
    
    db.commit()
    db.refresh(contract)
    return contract


def send_contract(db: Session, contract_id: str) -> Contract:
    """
    Send contract for signing.
    Only allowed if system is LIVE.
    """
    if not is_live():
        raise RuntimeError("Contract sending is only allowed in LIVE mode")
    
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise ValueError(f"Contract {contract_id} not found")
    
    if contract.state != "DRAFT":
        raise ValueError(f"Cannot send contract in {contract.state} state")
    
    return update_contract_state(db, contract_id, "SENT", actor="system")


def _log_event(db: Session, contract_id: str, event_type: str, actor: str = None, meta: dict = None):
    """Internal helper to log contract events."""
    event = ContractEvent(
        id=f"evt_{uuid.uuid4().hex[:12]}",
        contract_id=contract_id,
        event_type=event_type,
        actor=actor or "system",
        meta=meta or {}
    )
    db.add(event)
