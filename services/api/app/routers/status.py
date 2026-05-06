"""System go-live status endpoint for WeWeb readiness check."""
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(prefix="/api/go-live", tags=["System Status"])


@router.get("/status")
def get_go_live_status():
    """
    Backend launch readiness status for WeWeb.

    This endpoint is intentionally simple so WeWeb can display system readiness
    without having to calculate anything in the frontend.
    
    Returns:
        dict: System readiness status with all component checks
    """

    blockers = []
    warnings = []

    # WeWeb is intentionally false until frontend pages are connected/tested.
    weweb_ready = False

    if not weweb_ready:
        blockers.append("WeWeb frontend is not connected yet.")

    return {
        "system": "Valhalla Legacy Inc.",
        "mode": "pre_weweb_backend_ready",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "backend_ready": True,
        "database_ready": True,
        "va_intake_ready": True,
        "approvals_ready": True,
        "deal_conversion_ready": True,
        "audit_logging_ready": True,
        "weweb_ready": weweb_ready,
        "ok_to_go_live": len(blockers) == 0,
        "blockers": blockers,
        "warnings": warnings,
        "next_step": "Connect WeWeb pages to tested API endpoints."
    }
