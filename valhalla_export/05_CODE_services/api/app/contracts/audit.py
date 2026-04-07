"""Contract audit trail management."""
from app.contracts.events import record_event


def audit_created(contract_id, template_id):
    """Audit contract creation."""
    return record_event(
        contract_id,
        "CREATED",
        {"template_id": template_id}
    )


def audit_sent(contract_id, recipient):
    """Audit contract sent."""
    return record_event(
        contract_id,
        "SENT",
        {"recipient": recipient}
    )


def audit_signed(contract_id, signer):
    """Audit contract signed."""
    return record_event(
        contract_id,
        "SIGNED",
        {"signer": signer}
    )


def audit_executed(contract_id):
    """Audit contract executed."""
    return record_event(
        contract_id,
        "EXECUTED",
        {"timestamp": "now"}
    )


def get_contract_history(contract_id):
    """Get complete audit trail for contract."""
    from app.contracts.events import get_contract_events
    return get_contract_events(contract_id)
