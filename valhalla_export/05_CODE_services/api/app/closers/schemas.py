from pydantic import BaseModel, Field
from datetime import datetime


class CloserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    success_rate: float = 0.0
    last_interaction: datetime | None = None
    current_target: str | None = None


class CloserCreate(CloserBase):
    pass


class CloserResponse(CloserBase):
    id: int

    class Config:
        from_attributes = True
