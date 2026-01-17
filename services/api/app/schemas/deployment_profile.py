"""
PACK UB: Deployment Profile & Smoke Test Runner Schemas
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel


class DeploymentProfile(BaseModel):
    environment: str
    version: str
    timestamp: datetime


class SmokeTestResult(BaseModel):
    name: str
    endpoint: str
    ok: bool
    status_code: int
    detail: str | None = None


class SmokeTestReport(BaseModel):
    timestamp: datetime
    environment: str
    version: str
    results: List[SmokeTestResult]
    all_ok: bool
