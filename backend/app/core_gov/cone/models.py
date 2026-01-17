from pydantic import BaseModel, Field
from ..canon.canon import ConeBand

class ConeState(BaseModel):
    band: ConeBand = Field(default=ConeBand.B_CAUTION)
    reason: str = Field(default="Default to caution until proven stable")
    updated_at_utc: str = Field(default="")
    metrics: dict = Field(default_factory=dict)

class ConeDecision(BaseModel):
    allowed: bool
    band: ConeBand
    engine: str
    action: str
    reason: str
