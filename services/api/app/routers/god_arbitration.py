"""God Arbitration Router (Pack 82).

Provides endpoint to synthesize Heimdall & Loki stances into a unified recommendation.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.god_arbitrator import arbiter
from app.schemas.arbitration import ArbitrationRequest, ArbitrationResponse

router = APIRouter(prefix="/god", tags=["God Arbitration"])


@router.post(
    "/arbitrate",
    response_model=ArbitrationResponse,
    status_code=status.HTTP_200_OK,
)
def arbitrate(
    payload: ArbitrationRequest,
    db: Session = Depends(get_db),  # retained for future persistence / events
) -> ArbitrationResponse:
    """Arbitrate Heimdall and Loki outputs into a unified stance."""
    result = arbiter.arbitrate(
        heimdall_summary=payload.heimdall_summary,
        loki_summary=payload.loki_summary,
        heimdall_risk_tier=payload.heimdall_risk_tier,
        loki_risk_tier=payload.loki_risk_tier,
        dispute_context=payload.dispute_context,
        verdict_context=payload.verdict_context,
    )
    return ArbitrationResponse(**result.__dict__)
