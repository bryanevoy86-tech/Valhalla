# app/ai/agents/loki.py
from __future__ import annotations

from typing import Any, Dict, List

from app.ai.models import DecisionProposal, AgentVerdict


class LokiAgent:
    """
    Loki = second AI god:
      - More skeptical / conservative.
      - Looks for hidden risk in the proposal payload.
      - NEVER replaces Heimdall – provides a cross-check.
    """

    name: str = "Loki"

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
        warnings: List[str] = []

        # Basic rules (you can tune later):
        # - If very high risk or very large amount → default to NO.
        # - If moderate risk and moderate amount → cautious YES.
        if risk >= 0.8 or amount >= 1_000_000:
            approved = False
            confidence = 0.9
            reasons.append(
                f"High perceived risk ({risk:.2f}) or large amount ({amount:.2f})."
            )
            warnings.append("Conservative block: Loki recommends re-check with humans.")
        elif risk <= 0.4 and amount <= 100_000:
            approved = True
            confidence = 0.8
            reasons.append(
                f"Risk score is relatively low ({risk:.2f}) and amount is moderate ({amount:.2f})."
            )
        else:
            approved = False
            confidence = 0.7
            reasons.append(
                f"Ambiguous zone (risk={risk:.2f}, amount={amount:.2f}); "
                "Loki prefers to err on the side of caution."
            )
            warnings.append("Recommend manual review before proceeding.")

        return AgentVerdict(
            agent_name=cls.name,
            approved=approved,
            confidence=confidence,
            reasons=reasons,
            warnings=warnings,
            metadata={
                "risk_score": risk,
                "amount": amount,
                "domain": proposal.domain,
            },
        )
