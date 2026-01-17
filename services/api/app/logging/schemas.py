from datetime import datetime
from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: datetime
    action: str
    user_id: str
    details: str
