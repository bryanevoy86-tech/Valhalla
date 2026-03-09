from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel

class GoSession(BaseModel):
    active: bool
    started_at_utc: Optional[str] = None
    ended_at_utc: Optional[str] = None
    cone_band: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    snapshot: Optional[Dict[str, Any]] = None
