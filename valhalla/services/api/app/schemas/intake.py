from pydantic import BaseModel, Field, ConfigDict, condecimal
from typing import Optional
from datetime import datetime

class CapitalIn(BaseModel):
    source: str = Field(..., max_length=100)
    amount: condecimal(max_digits=18, decimal_places=2)
    currency: str = "CAD"
    note: Optional[str] = None

class CapitalOut(CapitalIn):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
