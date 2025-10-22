from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MetricIn(BaseModel):
    name: str = Field(..., max_length=100)
    value: float
    unit: Optional[str] = None
    tags: Optional[str] = None

class MetricOut(MetricIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
