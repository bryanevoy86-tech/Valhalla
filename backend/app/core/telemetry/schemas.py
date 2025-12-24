from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, Literal, Dict, Any

TelemetryType = Literal["decision", "action", "outcome", "anomaly", "error"]


class TelemetryEventIn(BaseModel):
    event_type: TelemetryType
    leg: str
    reference_id: Optional[str] = None  # e.g. export_job_id, deal_id, etc.
    payload: Dict[str, Any] = {}
