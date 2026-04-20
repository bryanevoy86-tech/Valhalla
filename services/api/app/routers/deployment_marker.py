"""
DEPLOYMENT MARKER - Updated 2026-04-19T02:50:00Z
This file proves when Render pulls the latest code from main.
If you can GET this endpoint and it returns this message, Render has deployed the latest code.
"""

from fastapi import APIRouter

router = APIRouter(tags=["deployment"])

@router.get("/deployment-marker")
def get_deployment_marker():
    """
    Prove that the latest code is deployed.
    Look for timestamp in response - should be 2026-04-19T02:50:00Z or later.
    """
    return {
        "status": "ok",
        "timestamp": "2026-04-19T02:50:00Z",
        "message": "Latest code from main branch (a675828) is deployed",
        "commit": "a675828",
        "endpoint": "GET /deployment-marker"
    }
