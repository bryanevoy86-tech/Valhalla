from pydantic import BaseModel
from typing import Optional


class HeimdallActionRequest(BaseModel):
    # core event
    source: str                  # "Heimdall", "worker", "api", "weweb"
    category: str                # "deal", "trust", "vault", "shield", etc.
    action: str                  # "created", "updated", "flagged", "triggered"
    message: str                 # human readable summary
    severity: str = "info"       # info / warn / critical

    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    payload: Optional[str] = None  # JSON/text

    # optional notification
    notify: bool = False
    notify_title: Optional[str] = None
    notify_audience: str = "king"
    notify_channel: str = "system"

    # optional compliance signal
    create_compliance_signal: bool = False
    compliance_deal_id: Optional[int] = None
    compliance_code: Optional[str] = None
    compliance_message: Optional[str] = None
    compliance_score: float = 0.0
