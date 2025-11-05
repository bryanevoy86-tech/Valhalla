from typing import Optional, List
from pydantic import BaseModel


class UserActivityIn(BaseModel):
    user_id: str
    action: str
    metadata: Optional[dict] = None


class UserActivityOut(BaseModel):
    user_id: str
    action: str
    timestamp: str
    metadata: Optional[dict] = None
