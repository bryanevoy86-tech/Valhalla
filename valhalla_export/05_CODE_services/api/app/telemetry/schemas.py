from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class TelemetryIn(BaseModel):
    event: str = Field(..., description='event key, e.g. builder.apply, deploy.start')
    level: str = Field('info', description='info|warn|error')
    actor: Optional[str] = Field(None, description='who/what triggered this')
    meta: Dict[str, Any] = {}

class TelemetryOut(TelemetryIn):
    id: int
    ts: datetime

class TelemetryQuery(BaseModel):
    event: Optional[str] = None
    level: Optional[str] = None
    actor: Optional[str] = None
    limit: int = 100
    offset: int = 0
