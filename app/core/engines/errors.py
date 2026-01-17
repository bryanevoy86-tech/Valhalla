class EngineError(Exception):
    pass


class EngineBlocked(EngineError):
    """
    Raised when an engine is blocked by state, runbook, or gates.
    """
    pass


class EngineTransitionDenied(EngineError):
    """
    Raised when an engine is not allowed to transition states.
    """
    pass
