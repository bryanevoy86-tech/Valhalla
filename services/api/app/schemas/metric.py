from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class MetricIn(BaseModel):
    name: str = Field(..., max_length=100)
    value: float
    unit: Optional[str] = None
    tags: Optional[str] = None

class MetricOut(MetricIn):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
