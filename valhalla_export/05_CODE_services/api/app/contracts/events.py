"""Contract events and audit trail."""
from datetime import datetime
from uuid import uuid4


class ContractEvent:
    """In-memory contract event model."""
    def __init__(self, contract_id, event, details=None):
        self.id = f"evt_{uuid4().hex[:12]}"
        self.contract_id = contract_id
        self.event = event
        self.details = details or {}
        self.created_at = datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "event": self.event,
            "details": self.details,
            "created_at": self.created_at.isoformat()
        }


# In-memory event storage (replace with DB in production)
_events = []


def record_event(contract_id, event, details=None):
    """Record a contract event."""
    evt = ContractEvent(contract_id, event, details)
    _events.append(evt)
    return evt.to_dict()


def get_contract_events(contract_id):
    """Get all events for a contract."""
    return [e.to_dict() for e in _events if e.contract_id == contract_id]


def get_all_events():
    """Get all contract events."""
    return [e.to_dict() for e in _events]
