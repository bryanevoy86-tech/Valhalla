from typing import List, Optional

from pydantic import AnyHttpUrl, BaseModel


class WebhookIn(BaseModel):
    name: str
    url: AnyHttpUrl
    secret: str
    is_active: bool = True
    events: List[str] = ["export.completed", "export.failed"]


class WebhookOut(WebhookIn):
    id: int


class EventOut(BaseModel):
    id: int
    event_type: str
    job_id: int
    payload: dict
    status: str
    attempts: int
    last_error: Optional[str] = None
