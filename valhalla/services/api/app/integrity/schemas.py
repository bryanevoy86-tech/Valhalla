"""Pack 59: Integrity + Telemetry - Schemas"""
from pydantic import BaseModel
from typing import Optional

class IntegrityIn(BaseModel):
    actor: str
    action: str
    scope: str
    ref_id: Optional[str] = None
    payload_json: Optional[str] = None

class TelemetryIn(BaseModel):
    category: str
    name: str
    latency_ms: Optional[int] = None
    ok: bool = True
    dim: Optional[str] = None
