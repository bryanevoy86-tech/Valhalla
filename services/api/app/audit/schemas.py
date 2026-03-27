from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime


class AuditEventCreate(BaseModel):
    # Core audit fields (mapped to DB columns)
    action: str
    entity_type: str  # "deal", "lead", etc.
    entity_id: int    # ID of the entity (deal_id, lead_id, etc.)
    previous_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = "system"
    notes: Optional[str] = None
    
    # Backward compatibility / extra fields (for reference in meta)
    actor: Optional[str] = None  # who performed the action
    target: Optional[str] = None  # what entity (e.g., "deal_1")
    result: Optional[str] = None  # "success", "rejected", etc.
    meta: Optional[Dict[str, Any]] = None  # arbitrary details

    class Config:
        # Allow extra fields
        extra = "allow"


class AuditEventResponse(BaseModel):
    id: int
    created_at: datetime
    action: str
    entity_type: str
    entity_id: int
    previous_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    user_id: str
    notes: Optional[str]

    class Config:
        from_attributes = True
