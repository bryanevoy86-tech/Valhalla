from pydantic import BaseModel


class AlertOut(BaseModel):
    alert_type: str
    message: str
    triggered_at: str
