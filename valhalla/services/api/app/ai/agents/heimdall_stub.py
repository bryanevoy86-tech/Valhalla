# app/ai/agents/heimdall_stub.py
from __future__ import annotations

from typing import Any, Dict, List

from app.ai.models import DecisionProposal, AgentVerdict


class HeimdallStub:
    """
    Temporary implementation so the arbitration engine has a primary agent.
    This version is slightly more optimistic than Loki.
    """

    name: str = "Heimdall"

    @classmethod
    def _extract_risk(cls, payload: Dict[str, Any]) -> float:
        raw = payload.get("risk_score", 0.5)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = 0.5
        return max(0.0, min(1.0, value))

    @classmethod
    def _extract_amount(cls, payload: Dict[str, Any]) -> float:
        raw = payload.get("amount", 0.0)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = 0.0
        return max(0.0, value)

    @classmethod
    def evaluate(cls, proposal: DecisionProposal) -> AgentVerdict:
        risk = cls._extract_risk(proposal.payload)
        amount = cls._extract_amount(proposal.payload)

        reasons: List[str] = []

        # Heimdall is allowed to be more assertive / growth-focused.
        if risk <= 0.7:
            approved = True
            confidence = 0.85
            reasons.append(
                f"Heimdall accepts calculated risk (risk={risk:.2f}, amount={amount:.2f})."
            )
        else:
            approved = False
            confidence = 0.9
            reasons.append(
                f"Risk too high even for Heimdall (risk={risk:.2f})."
            )

        return AgentVerdict(
            agent_name=cls.name,
            approved=approved,
            confidence=confidence,
            reasons=reasons,
            warnings=[],
            metadata={
                "risk_score": risk,
                "amount": amount,
                "domain": proposal.domain,
            },
        )
