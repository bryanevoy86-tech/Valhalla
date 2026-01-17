"""
P-AUDIT-2: Audit logging decorator for safe-calling audit store.

Provides audit() decorator to log function calls automatically.
"""
from functools import wraps
from typing import Any, Callable
from . import store


def audit(event_type: str) -> Callable:
    """
    Decorator that logs function calls to audit log.
    
    Args:
        event_type: Type of event to log
    
    Returns:
        Decorated function that logs calls
    
    Example:
        @audit("user_login")
        def login_user(user_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                # Log successful call
                try:
                    store.append(event_type, {
                        "function": func.__name__,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100],
                        "status": "success"
                    })
                except Exception:
                    pass  # Silently fail audit logging
                return result
            except Exception as e:
                # Log failed call
                try:
                    store.append(event_type, {
                        "function": func.__name__,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100],
                        "status": "error",
                        "error": str(e)[:100]
                    })
                except Exception:
                    pass  # Silently fail audit logging
                raise
        return wrapper
    return decorator
