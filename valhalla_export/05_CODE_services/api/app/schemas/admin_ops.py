"""
PACK UF: Admin Ops Console Schemas
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel


class AdminActionRequest(BaseModel):
    action: str
    payload: Optional[Dict[str, Any]] = None


class AdminActionResponse(BaseModel):
    action: str
    ok: bool
    detail: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
