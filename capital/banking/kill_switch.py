"""
Global stop – instant freeze
"""

KILL_SWITCH = {"enabled": False}


def activate_kill_switch():
    """Activate the kill switch – all transfers freeze immediately."""
    KILL_SWITCH["enabled"] = True


def deactivate_kill_switch():
    """Deactivate the kill switch – resume normal operations."""
    KILL_SWITCH["enabled"] = False


def is_killed():
    """Check if the kill switch is active."""
    return KILL_SWITCH["enabled"]
