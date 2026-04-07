"""Heimdall Authority - gatekeeping for system activation.

Evaluates readiness checks and determines if activation is allowed.
Respects runtime mode flags.
"""
from app.core.runtime_flags import RUNTIME_MODE, RuntimeMode


class HeimdallAuthority:
    """Authority gate for system activation and execution."""
    
    def __init__(self):
        self.ready = False
        self.reasons = []  # List of checks that failed
    
    def evaluate(self, checks: dict) -> bool:
        """
        Evaluate a dict of checks.
        
        Args:
            checks: dict where keys are check names, values are booleans (True = pass)
        
        Returns:
            True if all checks pass, False otherwise
        """
        self.reasons = [k for k, v in checks.items() if not v]
        self.ready = len(self.reasons) == 0
        return self.ready
    
    def activation_allowed(self) -> bool:
        """
        Check if activation is allowed.
        
        Returns True only if:
        1. All readiness checks passed (self.ready == True)
        2. Runtime mode is ARMED or LIVE
        """
        return self.ready and RUNTIME_MODE in (RuntimeMode.ARMED, RuntimeMode.LIVE)
    
    def get_status(self) -> dict:
        """Return current status and reasons for any failures."""
        return {
            "ready": self.ready,
            "failures": self.reasons,
            "runtime_mode": RUNTIME_MODE.value,
            "activation_allowed": self.activation_allowed()
        }
    
    def is_active(self) -> bool:
        """Check if Heimdall is actively gating (armed or live)."""
        return self.ready and self.activation_allowed()


# Global Heimdall instance
HEIMDALL = HeimdallAuthority()


def is_live() -> bool:
    """Check if system is in LIVE mode for executing real transactions."""
    return RUNTIME_MODE == RuntimeMode.LIVE
