from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OutcomeRecord:
    """
    Closed-loop evidence record.
    Use this for leads, deals, buyers, scripts, etc.
    """
    entity_type: str  # "lead" | "deal" | "buyer" | etc.
    entity_id: str

    outcome: str  # "won" | "lost" | "dead" | "paused" | "unknown"
    reason: str   # e.g. "price", "timing", "motivation", "bad_data", "no_response"
    notes: str = ""
    evidence_ref: Optional[str] = None  # link/id to doc, message, screenshot, etc.

    recorded_at: str = ""  # ISO

    def normalize(self) -> "OutcomeRecord":
        if not self.recorded_at:
            self.recorded_at = datetime.utcnow().isoformat() + "Z"
        self.entity_type = self.entity_type.strip().lower()
        self.outcome = self.outcome.strip().lower()
        self.reason = self.reason.strip().lower()
        return self
