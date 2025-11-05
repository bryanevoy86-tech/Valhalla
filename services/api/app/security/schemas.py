from pydantic import BaseModel


class TwoFactorAuthOut(BaseModel):
    user_id: str
    verified: bool
    token_expiry: str


class RateLimitOut(BaseModel):
    request_count: int
    reset_time: str
