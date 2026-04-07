from app.core_flags.flags import is_enabled

def warm_startup():
    checks = {
        "launch_core_only": is_enabled("launch_core_only", False),
        "enable_eia_tracking": is_enabled("enable_eia_tracking", False),
        "require_eia_compliance": is_enabled("require_eia_compliance", False),
    }

    checks["ready"] = all(checks.values())
    return checks
    """
    Warm startup sequence - validates everything loads correctly.
    """
    try:
        ready = system_ready_check()
        preflight = preflight_checks()
        
        return {
            "status": "STARTUP_COMPLETE",
            "system_ready": ready["status"],
            "all_checks_passed": preflight["all_passed"],
            "phase": "PHASE_1_LOCKED",
            "timestamp": "now"
        }
    except Exception as e:
        return {
            "status": "STARTUP_FAILED",
            "error": str(e),
            "phase": "PHASE_1",
            "requires_intervention": True
        }
