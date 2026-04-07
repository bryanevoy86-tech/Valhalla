"""Admin runtime control - arm and go live switches."""
from app.core import runtime_flags


def get_current_mode() -> dict:
    """Get the current runtime mode."""
    return {
        "mode": runtime_flags.RUNTIME_MODE.value,
        "is_sandbox": runtime_flags.is_sandbox(),
        "is_armed": runtime_flags.is_armed(),
        "is_live": runtime_flags.is_live()
    }


def arm_system(authorized_by: str = None) -> dict:
    """
    Arm the system (move from SANDBOX to ARMED).
    
    In ARMED mode, system is ready to execute but waiting for final authorization.
    """
    if runtime_flags.RUNTIME_MODE == runtime_flags.RuntimeMode.SANDBOX:
        runtime_flags.RUNTIME_MODE = runtime_flags.RuntimeMode.ARMED
        return {
            "success": True,
            "previous_mode": "sandbox",
            "new_mode": "armed",
            "authorized_by": authorized_by,
            "message": "System armed. Ready to go live with authorization."
        }
    
    return {
        "success": False,
        "current_mode": runtime_flags.RUNTIME_MODE.value,
        "message": f"Cannot arm from {runtime_flags.RUNTIME_MODE.value} mode"
    }


def go_live(authorized_by: str = None, authorization_token: str = None) -> dict:
    """
    Go LIVE - full system authorization.
    
    WARNING: This enables real transactions, payments, and live executions.
    Requires explicit authorization and optional token verification.
    """
    if runtime_flags.RUNTIME_MODE == runtime_flags.RuntimeMode.ARMED:
        runtime_flags.RUNTIME_MODE = runtime_flags.RuntimeMode.LIVE
        return {
            "success": True,
            "previous_mode": "armed",
            "new_mode": "live",
            "authorized_by": authorized_by,
            "message": "🚀 SYSTEM IS LIVE - Full execution authorized",
            "warning": "All transactions are now LIVE. This cannot be undone until restart."
        }
    elif runtime_flags.RUNTIME_MODE == runtime_flags.RuntimeMode.SANDBOX:
        return {
            "success": False,
            "current_mode": "sandbox",
            "message": "Must ARM system before going LIVE"
        }
    
    return {
        "success": False,
        "current_mode": runtime_flags.RUNTIME_MODE.value,
        "message": f"System is already in {runtime_flags.RUNTIME_MODE.value} mode"
    }


def return_to_sandbox(authorized_by: str = None) -> dict:
    """
    Return to SANDBOX mode (for testing/reset).
    
    Only allowed if not already LIVE.
    """
    if runtime_flags.RUNTIME_MODE == runtime_flags.RuntimeMode.LIVE:
        return {
            "success": False,
            "current_mode": "live",
            "message": "Cannot return from LIVE to SANDBOX (restart required)"
        }
    
    previous_mode = runtime_flags.RUNTIME_MODE.value
    runtime_flags.RUNTIME_MODE = runtime_flags.RuntimeMode.SANDBOX
    
    return {
        "success": True,
        "previous_mode": previous_mode,
        "new_mode": "sandbox",
        "authorized_by": authorized_by,
        "message": "Returned to SANDBOX mode"
    }


def get_runtime_status() -> dict:
    """Get complete runtime status."""
    return {
        "mode": runtime_flags.RUNTIME_MODE.value,
        "is_sandbox": runtime_flags.is_sandbox(),
        "is_armed": runtime_flags.is_armed(),
        "is_live": runtime_flags.is_live(),
        "status": {
            "can_execute_real_transactions": runtime_flags.is_live(),
            "can_make_offers": runtime_flags.is_armed(),
            "can_send_contracts": runtime_flags.is_live(),
            "can_process_payments": runtime_flags.is_live()
        }
    }
