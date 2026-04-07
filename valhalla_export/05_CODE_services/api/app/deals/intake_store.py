"""
Module 69: Lead Intake (Deals) Store
In-memory storage for deal leads from various sources.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List
import uuid
from datetime import datetime


@dataclass
class DealLead:
    """Deal lead from intake."""
    id: str
    source: str
    address: str
    city: str | None = None
    state: str | None = None
    asking_price: int | None = None
    arv: int | None = None
    repairs: int | None = None
    notes: str | None = None
    created_at: str = ""


class DealIntakeStore:
    """In-memory store for deal leads."""
    
    def __init__(self) -> None:
        """Initialize empty deal intake store."""
        self._leads: Dict[str, DealLead] = {}

    def create(self, payload: dict) -> dict:
        """
        Create new deal lead.
        
        Args:
            payload: Lead data dict
                {
                    "source": "direct",
                    "address": "123 Main St",
                    "city": "Denver",
                    "state": "CO",
                    "asking_price": 250000,
                    "arv": 350000,
                    "repairs": 30000,
                    "notes": "Off-market lead"
                }
        
        Returns:
            dict: Created lead data
        """
        lead_id = str(uuid.uuid4())
        payload["id"] = lead_id
        payload["created_at"] = datetime.utcnow().isoformat()
        lead = DealLead(**payload)
        self._leads[lead_id] = lead
        return asdict(lead)

    def list(self) -> List[dict]:
        """
        List all deal leads.
        
        Returns:
            List[dict]: List of lead dictionaries
        """
        return [asdict(l) for l in self._leads.values()]


# Global deal intake store
LEADS = DealIntakeStore()
