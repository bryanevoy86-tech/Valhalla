"""System Health Endpoint Schemas"""
from typing import List, Optional

from pydantic import BaseModel


class ServiceStatus(BaseModel):
    name: str
    status: str  # OK / DEGRADED / DOWN
    latency_ms: Optional[float] = None
    detail: Optional[str] = None


class DatabaseStatus(BaseModel):
    status: str
    connections: Optional[int] = None
    slow_queries: Optional[int] = None


class QueueStatus(BaseModel):
    status: str
    pending_jobs: Optional[int] = None
    failed_jobs: Optional[int] = None


class SystemHealthSummary(BaseModel):
    status: str  # OK / DEGRADED / DOWN
    services: List[ServiceStatus]
    db: DatabaseStatus
    queue: QueueStatus
    notes: list[str] = []
