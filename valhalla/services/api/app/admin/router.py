"""Admin router - system activation endpoints."""
from fastapi import APIRouter, HTTPException
from app.admin.runtime import arm_system, go_live, return_to_sandbox, get_current_mode
from app.admin.override import owner_override, emergency_shutdown
from app.admin.activation import attempt_go_live

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status")
def get_status():
    """Get current system status."""
    return get_current_mode()


@router.post("/arm")
def arm_endpoint():
    """Arm the system."""
    return arm_system()


@router.post("/go-live")
def go_live_endpoint():
    """Go live (activate system for production)."""
    return go_live()


@router.post("/return-to-sandbox")
def sandbox_endpoint():
    """Emergency: return to sandbox mode."""
    return return_to_sandbox()


@router.post("/activate")
def activate_endpoint():
    """Attempt full activation after all checks."""
    return attempt_go_live()


@router.post("/owner-override")
def override_endpoint(password: str):
    """Owner override for emergency access."""
    return owner_override(password)


@router.post("/emergency-shutdown")
def emergency_endpoint(password: str):
    """Emergency shutdown."""
    return emergency_shutdown(password)
