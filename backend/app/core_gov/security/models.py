from pydantic import BaseModel
from typing import List

class Identity(BaseModel):
    user_id: str
    email: str | None = None
    scopes: List[str] = []
    is_active_subscription: bool = True
