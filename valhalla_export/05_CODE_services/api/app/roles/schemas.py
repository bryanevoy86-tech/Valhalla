from typing import List
from pydantic import BaseModel


class RoleOut(BaseModel):
    role: str
    permissions: List[str]
    created_at: str
