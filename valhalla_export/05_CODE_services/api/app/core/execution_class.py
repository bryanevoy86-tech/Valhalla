"""
Execution classification for endpoints.

Prime intent:
- Do NOT redesign modules.
- Add a control-plane label so governance can enforce go-live without breaking observability.

Classes:
- OBSERVE_ONLY: dashboards, health, status, read-only views, governance endpoints
- SANDBOX_EXEC: sandbox runners, simulations, test-only execution
- PROD_EXEC: endpoints that mutate real state, trigger actions, send comms, move capital, etc.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, TypeVar, Any, Optional

F = TypeVar("F", bound=Callable[..., Any])


class ExecClass(str, Enum):
    OBSERVE_ONLY = "OBSERVE_ONLY"
    SANDBOX_EXEC = "SANDBOX_EXEC"
    PROD_EXEC = "PROD_EXEC"


def set_exec_class(exec_class: ExecClass) -> Callable[[F], F]:
    """
    Decorator to tag a FastAPI endpoint with an execution class.

    Usage:
        @router.post("/do-thing")
        @set_exec_class(ExecClass.PROD_EXEC)
        def do_thing(...):
            ...
    """
    def decorator(fn: F) -> F:
        setattr(fn, "__exec_class__", exec_class.value)
        return fn
    return decorator


def get_exec_class(endpoint: Optional[Callable[..., Any]]) -> str:
    """
    Returns exec class string for an endpoint (defaults to OBSERVE_ONLY).
    """
    if endpoint is None:
        return ExecClass.OBSERVE_ONLY.value
    return getattr(endpoint, "__exec_class__", ExecClass.OBSERVE_ONLY.value)
