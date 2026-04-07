"""
Module 66: System Activation Flag
Global system activation state.
"""
from typing import Dict, Any

# Global system activation state
SYSTEM_ACTIVE = False
SYSTEM_MODE = "SANDBOX"  # SANDBOX, ARMED, or LIVE


def activate():
    """
    Activate the system for autonomous operations.
    
    Returns:
        dict: Activation result
    """
    global SYSTEM_ACTIVE, SYSTEM_MODE
    SYSTEM_ACTIVE = True
    SYSTEM_MODE = "LIVE"
    
    return {
        "status": "activated",
        "active": SYSTEM_ACTIVE,
        "mode": SYSTEM_MODE,
        "message": "System is now LIVE - autonomous operations active"
    }


def deactivate():
    """
    Deactivate the system.
    
    Returns:
        dict: Deactivation result
    """
    global SYSTEM_ACTIVE, SYSTEM_MODE
    SYSTEM_ACTIVE = False
    SYSTEM_MODE = "SANDBOX"
    
    return {
        "status": "deactivated",
        "active": SYSTEM_ACTIVE,
        "mode": SYSTEM_MODE,
        "message": "System is now SANDBOX - autonomous operations disabled"
    }


def is_active() -> bool:
    """
    Check if system is active.
    
    Returns:
        bool: True if active
    """
    return SYSTEM_ACTIVE


def get_mode() -> str:
    """
    Get current system mode.
    
    Returns:
        str: Mode (SANDBOX, ARMED, or LIVE)
    """
    return SYSTEM_MODE


def set_mode(mode: str) -> Dict[str, Any]:
    """
    Set system mode.
    
    Args:
        mode: Mode (SANDBOX, ARMED, or LIVE)
    
    Returns:
        dict: Mode set result
    """
    global SYSTEM_ACTIVE, SYSTEM_MODE
    
    valid_modes = ["SANDBOX", "ARMED", "LIVE"]
    
    if mode not in valid_modes:
        return {
            "status": "error",
            "message": f"Invalid mode. Valid modes: {valid_modes}"
        }
    
    SYSTEM_MODE = mode
    SYSTEM_ACTIVE = (mode == "LIVE")
    
    return {
        "status": "success",
        "mode": SYSTEM_MODE,
        "active": SYSTEM_ACTIVE,
        "message": f"System mode set to {mode}"
    }


def get_status() -> Dict[str, Any]:
    """
    Get system activation status.
    
    Returns:
        dict: Status
    """
    return {
        "active": SYSTEM_ACTIVE,
        "mode": SYSTEM_MODE,
        "operations_enabled": SYSTEM_ACTIVE,
        "autonomous": SYSTEM_ACTIVE
    }
