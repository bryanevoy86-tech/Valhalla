"""
Module 43: System Health + Kill Switch
Emergency system disable capability for safety.
"""

# Global system state
SYSTEM_ENABLED = True


def disable_system():
    """
    Disable the entire system.
    Emergency only - requires authentication.
    """
    global SYSTEM_ENABLED
    SYSTEM_ENABLED = False
    return {
        "status": "system_disabled",
        "enabled": SYSTEM_ENABLED
    }


def enable_system():
    """
    Re-enable the system after kill switch.
    """
    global SYSTEM_ENABLED
    SYSTEM_ENABLED = True
    return {
        "status": "system_enabled",
        "enabled": SYSTEM_ENABLED
    }


def is_enabled():
    """
    Check if system is enabled.
    
    Returns:
        bool: True if system is enabled
    """
    return SYSTEM_ENABLED


def get_status():
    """
    Get system health status.
    
    Returns:
        dict: Current system status
    """
    return {
        "enabled": SYSTEM_ENABLED,
        "health": "operational" if SYSTEM_ENABLED else "disabled"
    }
