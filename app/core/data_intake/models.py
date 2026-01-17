from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class IntakeItem:
    """
    RAW intake item. Starts in QUARANTINE by default.
    'payload' can hold any shape of data (lead, buyer, listing, etc.)
    """
    item_id: str
    source: str  # e.g. "kijiji", "facebook", "manual", "csv_import"
    entity_type: str  # "lead" | "buyer" | "listing" | etc.
    payload: Dict[str, Any]

    trust_tier: str = "T0"     # T0..T4 (locked concept)
    status: str = "QUARANTINE" # QUARANTINE | CLEAN | REJECTED

    evidence_ref: Optional[str] = None
    created_at: str = ""

    def normalize(self) -> "IntakeItem":
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"
        self.source = self.source.strip().lower()
        self.entity_type = self.entity_type.strip().lower()
        self.status = self.status.strip().upper()
        self.trust_tier = self.trust_tier.strip().upper()
        return self
