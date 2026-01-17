from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ResortBookingCreate(BaseModel):
    guest_name: str
    check_in: datetime
    check_out: datetime
    room_type: str
    base_price: float

class ResortBookingUpdate(BaseModel):
    status: Optional[str]
    dynamic_price: Optional[float]

class ResortBookingOut(ResortBookingCreate):
    id: int
    dynamic_price: float
    status: str

    class Config:
        orm_mode = True
