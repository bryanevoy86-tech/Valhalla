"""Compatibility alias for legacy SimpleContract imports."""

from app.models.contracts import Contract

SimpleContract = Contract

__all__ = ["SimpleContract"]
