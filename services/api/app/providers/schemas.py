from pydantic import BaseModel, ConfigDict
from typing import Optional


class TokenCreate(BaseModel):
    provider: str
    account_ref: Optional[str] = None
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None
    scopes: Optional[str] = None


class TokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    provider: str
    account_ref: Optional[str]


class WebhookIn(BaseModel):
    event_type: str
    payload: dict
    signature: Optional[str] = None
