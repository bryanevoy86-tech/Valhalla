"""System activation - orchestrate go-live sequence."""
from app.core.runtime_flags import RuntimeMode, set_runtime_mode, is_live
from app.heimdall.readiness import readiness_checks, is_ready_to_go_live
from app.heimdall.authority import HEIMDALL


def attempt_go_live() -> dict:
    """
    Attempt to transition system from SANDBOX to LIVE.
    
    Validates all checks pass before arming and going live.
    
    Returns:
        dict with result and any blocking issues
    """
    # Check readiness
    checks = readiness_checks()
    blocking_checks = [k for k, v in checks.items() if not v and k in [
        "database_connected",
        "s3_configured",
        "contracts_templates_loaded",
        "heimdall_authority_ready",
        "audit_logging_enabled",
        "all_modules_loaded"
    ]]
    
    if blocking_checks:
        return {
            "status": "failed",
            "reason": "Blocking readiness checks failed",
            "blocking_checks": blocking_checks,
            "action": "Fix above checks before attempting go-live"
        }
    
    # Step 1: Arm the system
    try:
        HEIMDALL.activate()
        current_mode = RuntimeMode.ARMED
    except Exception as e:
        return {
            "status": "failed",
            "reason": f"Failed to arm system: {str(e)}",
            "step": "activation"
        }
    
    # Step 2: Go live
    try:
        set_runtime_mode(RuntimeMode.LIVE)
        current_mode = RuntimeMode.LIVE
    except Exception as e:
        return {
            "status": "failed",
            "reason": f"Failed to go live: {str(e)}",
            "step": "go_live"
        }
    
    return {
        "status": "success",
        "mode": "live",
        "message": "System successfully transitioned to LIVE mode",
        "time": None
    }


def return_to_sandbox() -> dict:
    """Return system to sandbox mode."""
    try:
        set_runtime_mode(RuntimeMode.SANDBOX)
        return {
            "status": "success",
            "mode": "sandbox",
            "message": "System returned to SANDBOX mode"
        }
    except Exception as e:
        return {
            "status": "failed",
            "reason": str(e)
        }


def get_system_status() -> dict:
    """Get current system status."""
    return {
        "live": is_live(),
        "mode": "live" if is_live() else "sandbox",
        "heimdall_armed": HEIMDALL.is_active(),
        "readiness": is_ready_to_go_live()
    }
