from typing import Optional
from pydantic import BaseModel


class HealthCheckOut(BaseModel):
    service: str
    status: str
    last_checked: str
    recovery_action_taken: Optional[str] = None
