"""
Module 50: System State Endpoint
REST API for monitoring system state and health.
"""
from fastapi import APIRouter
from app.system.kill_switch import get_status, disable_system, enable_system, is_enabled
from app.heimdall.authority import HEIMDALL

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/state", response_description="System state")
def get_system_state():
    """
    Get current system state.
    
    Returns:
        dict: System state (enabled, heimdall status, etc.)
    """
    return {
        "system": {
            "enabled": is_enabled(),
            "status": get_status()
        },
        "heimdall": {
            "active": HEIMDALL.is_active() if hasattr(HEIMDALL, 'is_active') else None
        }
    }


@router.get("/health", response_description="System health")
def health_check():
    """
    Health check endpoint.
    Always available even if system is disabled.
    """
    return {
        "status": "ok",
        "system_enabled": is_enabled()
    }


@router.post("/disable", response_description="Disable system")
def disable_endpoint():
    """
    Disable system (kill switch).
    Emergency only.
    """
    return disable_system()


@router.post("/enable", response_description="Enable system")
def enable_endpoint():
    """
    Re-enable system after kill switch.
    """
    return enable_system()
