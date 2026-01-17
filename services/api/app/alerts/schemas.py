from pydantic import BaseModel


class AlertOut(BaseModel):
    alert_type: str
    message: str
    triggered_at: str


class AlertResponseOut(BaseModel):
    action_type: str
    message: str
    triggered_at: str
    status: str
