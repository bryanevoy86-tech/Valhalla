"""
PACK UB: Deployment Profile & Smoke Test Runner Service
"""

from datetime import datetime
from typing import List

import httpx
from sqlalchemy.orm import Session

from app.models.system_metadata import SystemMetadata
from app.schemas.deployment_profile import (
    DeploymentProfile,
    SmokeTestResult,
    SmokeTestReport,
)


def get_deployment_profile(db: Session, environment: str) -> DeploymentProfile:
    meta = db.query(SystemMetadata).filter(SystemMetadata.id == 1).first()
    version = meta.version if meta else "0.0.0"
    return DeploymentProfile(
        environment=environment,
        version=version,
        timestamp=datetime.utcnow(),
    )


async def run_smoke_tests(
    base_url: str,
    environment: str,
    version: str,
) -> SmokeTestReport:
    # Key endpoints to ping
    tests = [
        ("health_live", "/system/health/live"),
        ("health_ready", "/system/health/ready"),
        ("status", "/system/status/"),
        ("security_dashboard", "/security/dashboard/"),
    ]

    results: List[SmokeTestResult] = []
    async with httpx.AsyncClient(base_url=base_url, timeout=5.0) as client:
        for name, endpoint in tests:
            try:
                resp = await client.get(endpoint)
                ok = resp.status_code == 200
                detail = None if ok else f"Unexpected status {resp.status_code}"
                results.append(
                    SmokeTestResult(
                        name=name,
                        endpoint=endpoint,
                        ok=ok,
                        status_code=resp.status_code,
                        detail=detail,
                    )
                )
            except Exception as e:
                results.append(
                    SmokeTestResult(
                        name=name,
                        endpoint=endpoint,
                        ok=False,
                        status_code=0,
                        detail=str(e),
                    )
                )

    all_ok = all(r.ok for r in results)
    return SmokeTestReport(
        timestamp=datetime.utcnow(),
        environment=environment,
        version=version,
        results=results,
        all_ok=all_ok,
    )
