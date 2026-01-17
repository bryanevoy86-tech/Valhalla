# app/api/v1/arbitration.py
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_admin_user
from app.ai.models import DecisionProposal, ArbitrationOutcome
from app.ai.agents.heimdall_stub import HeimdallStub
from app.ai.agents.loki import LokiAgent
from app.ai.arbitration import ArbitrationEngine

router = APIRouter(prefix="/arbitration", tags=["arbitration"])


@router.post("/decision", response_model=ArbitrationOutcome)
async def arbitrate_decision(
    proposal: DecisionProposal,
    user=Depends(get_current_admin_user),
):
    """
    Run a proposal through Heimdall (primary) + Loki (secondary),
    then combine via ArbitrationEngine.

    Example payload:
    {
      "id": "deal-123",
      "domain": "real_estate_deal",
      "payload": {
        "risk_score": 0.65,
        "amount": 250000,
        "context": {...}
      }
    }
    """
    primary = HeimdallStub.evaluate(proposal)
    secondary = LokiAgent.evaluate(proposal)
    outcome = ArbitrationEngine.arbitrate(proposal, primary, secondary)
    return outcome


@router.get("/ping")
async def arbitration_ping(user=Depends(get_current_admin_user)):
    """
    Simple health check for the arbitration stack.
    """
    return {
        "status": "ok",
        "stack": {
            "primary": HeimdallStub.name,
            "secondary": LokiAgent.name,
        },
    }
