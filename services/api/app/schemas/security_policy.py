"""
PACK TQ: Security Policy Schemas
Request/response models for policy and blocklist management.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SecurityPolicyUpdate(BaseModel):
    """Update security policy settings."""
    default_mode: Optional[str] = None
    auto_elevate: Optional[bool] = None
    auto_lockdown: Optional[bool] = None
    max_failed_auth: Optional[int] = None
    max_scan_events: Optional[int] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SecurityPolicyOut(BaseModel):
    """Security policy response."""
    id: int
    default_mode: str
    auto_elevate: bool
    auto_lockdown: bool
    max_failed_auth: int
    max_scan_events: int
    notes: Optional[str]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlockedEntityCreate(BaseModel):
    """Create a blocked entity."""
    entity_type: str        # ip, user, api_key
    value: str
    reason: str
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BlockedEntityOut(BaseModel):
    """Blocked entity response."""
    id: int
    entity_type: str
    value: str
    reason: str
    active: bool
    created_at: datetime
    expires_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class BlockedEntityList(BaseModel):
    """List of blocked entities."""
    total: int
    active: int
    items: List[BlockedEntityOut]

    model_config = ConfigDict(from_attributes=True)
