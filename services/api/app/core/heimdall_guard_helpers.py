"""Heimdall Guard helper functions for drop-in integration.

This is the "two-line" drop-in you'll use in execution endpoints.
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy.orm import Session
from app.services.heimdall_governance import assert_prod_eligible


def heimdall_require_prod_eligible(
    db: Session,
    recommendation_id: int,
    actor: Optional[str] = None,
    correlation_id: Optional[str] = None,
):
    """
    Enforce: Heimdall may recommend, but production execution may only proceed
    if recommendation is prod_eligible per charter.
    """
    return assert_prod_eligible(db, recommendation_id=recommendation_id, actor=actor, correlation_id=correlation_id)
