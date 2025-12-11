"""PACK 75: Integrity & Telemetry Schemas
Pydantic models for integrity events and telemetry metrics.
"""

from pydantic import BaseModel
from typing import Optional


class IntegrityEventBase(BaseModel):
    event_type: str
    actor: Optional[str] = None
    payload: str
    signature: Optional[str] = None


class IntegrityEventCreate(IntegrityEventBase):
    pass


class IntegrityEventOut(IntegrityEventBase):
    id: int

    class Config:
        from_attributes = True


class TelemetryMetricBase(BaseModel):
    metric_name: str
    value: float
    context: Optional[str] = None


class TelemetryMetricCreate(TelemetryMetricBase):
    pass


class TelemetryMetricOut(TelemetryMetricBase):
    id: int

    class Config:
        from_attributes = True
