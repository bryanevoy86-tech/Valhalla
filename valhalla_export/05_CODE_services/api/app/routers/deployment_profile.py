"""
PACK UB: Deployment Profile & Smoke Test Runner Router
Prefix: /system/deploy
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.deployment_profile import DeploymentProfile, SmokeTestReport
from app.services.deployment_profile import get_deployment_profile, run_smoke_tests

router = APIRouter(prefix="/system/deploy", tags=["Deployment"])


@router.get("/profile", response_model=DeploymentProfile)
def deployment_profile_endpoint(
    environment: str = Query("dev"),
    db: Session = Depends(get_db),
):
    """
    Returns deployment profile info (env + version).

    Heimdall can call this to know:
    - Where it's running (dev/stage/prod)
    - Which version of the backend it's talking to
    """
    return get_deployment_profile(db, environment=environment)


@router.get("/smoke", response_model=SmokeTestReport)
async def smoke_test_endpoint(
    base_url: str = Query(..., description="Base URL of this deployment, e.g. https://api.example.com"),
    environment: str = Query("dev"),
    db: Session = Depends(get_db),
):
    """
    Run a small set of smoke tests against key endpoints.

    This is safe to call after deployment to confirm the backend is alive.
    """
    profile = get_deployment_profile(db, environment=environment)
    report = await run_smoke_tests(base_url=base_url, environment=environment, version=profile.version)
    return report
