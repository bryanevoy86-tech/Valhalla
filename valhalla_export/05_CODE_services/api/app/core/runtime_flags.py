"""Global runtime mode flags - controls system activation levels.

Three modes:
- SANDBOX: No real effects, safe for testing
- ARMED: Ready to execute but awaiting authorization
- LIVE: Full execution authorization, real effects
"""
from enum import Enum


class RuntimeMode(str, Enum):
    SANDBOX = "sandbox"
    ARMED = "armed"
    LIVE = "live"


# Global runtime mode (start in SANDBOX for safety)
RUNTIME_MODE = RuntimeMode.SANDBOX


def is_live():
    """Check if system is in LIVE mode (full execution)."""
    return RUNTIME_MODE == RuntimeMode.LIVE


def is_armed():
    """Check if system is ARMED or LIVE (ready to execute)."""
    return RUNTIME_MODE in (RuntimeMode.ARMED, RuntimeMode.LIVE)


def is_sandbox():
    """Check if system is in SANDBOX mode (no real effects)."""
    return RUNTIME_MODE == RuntimeMode.SANDBOX


def set_runtime_mode(mode: RuntimeMode):
    """Set the runtime mode. Compatibility function."""
    global RUNTIME_MODE
    RUNTIME_MODE = mode
    return RUNTIME_MODE

