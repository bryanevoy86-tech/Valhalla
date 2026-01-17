"""
Telemetry schemas for logging events and errors.
"""

from pydantic import BaseModel
from typing import Optional


class TelemetryIn(BaseModel):
    """Input schema for logging telemetry events"""
    kind: str
    message: Optional[str] = None
    meta_json: Optional[str] = None
