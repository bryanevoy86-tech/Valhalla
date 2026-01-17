"""
PACK TT: Security Dashboard Schemas
Request/response models for unified security view.
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict


class SecurityModeSnapshot(BaseModel):
    """Current security mode snapshot."""
    mode: str               # normal, elevated, lockdown
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityIncidentSnapshot(BaseModel):
    """Recent security incidents summary."""
    total_open: int
    critical: int
    high: int
    medium: int
    low: int

    model_config = ConfigDict(from_attributes=True)


class BlocklistSnapshot(BaseModel):
    """Active blocklist summary."""
    total_blocked: int
    ips: int
    users: int
    api_keys: int

    model_config = ConfigDict(from_attributes=True)


class HoneypotSnapshot(BaseModel):
    """Honeypot telemetry summary."""
    total_instances: int
    active_instances: int
    recent_events: int
    threats_detected: int

    model_config = ConfigDict(from_attributes=True)


class ActionRequestSnapshot(BaseModel):
    """Pending actions summary."""
    total_pending: int
    pending_by_type: dict   # { action_type: count }

    model_config = ConfigDict(from_attributes=True)


class SecurityDashboardSnapshot(BaseModel):
    """Unified security dashboard."""
    timestamp: datetime
    security_mode: SecurityModeSnapshot
    incidents: SecurityIncidentSnapshot
    blocklist: BlocklistSnapshot
    honeypot: HoneypotSnapshot
    action_requests: ActionRequestSnapshot
    last_update: datetime

    model_config = ConfigDict(from_attributes=True)
