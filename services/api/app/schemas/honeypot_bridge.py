"""
PACK TS: Honeypot Bridge Schemas
Request/response models for honeypot management and telemetry.
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class HoneypotInstanceCreate(BaseModel):
    """Create a honeypot instance."""
    name: str
    honeypot_type: str      # ssh, web, database, custom
    location: Optional[str] = None
    metadata: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class HoneypotInstanceOut(BaseModel):
    """Honeypot instance response."""
    id: int
    created_at: datetime
    name: str
    api_key: str
    honeypot_type: str
    location: Optional[str]
    active: bool
    metadata: Optional[dict]

    model_config = ConfigDict(from_attributes=True)


class HoneypotEventCreate(BaseModel):
    """Record a honeypot event (via X-HONEYPOT-KEY header)."""
    source_ip: str
    event_type: str         # connection, auth_attempt, exploitation, scan
    payload: Optional[dict] = None
    detected_threat: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HoneypotEventOut(BaseModel):
    """Honeypot event response."""
    id: int
    created_at: datetime
    honeypot_id: int
    source_ip: str
    event_type: str
    payload: Optional[dict]
    detected_threat: Optional[str]
    processed: bool

    model_config = ConfigDict(from_attributes=True)


class HoneypotEventList(BaseModel):
    """List of honeypot events."""
    total: int
    unprocessed: int
    items: List[HoneypotEventOut]

    model_config = ConfigDict(from_attributes=True)
