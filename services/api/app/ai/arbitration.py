# app/ai/arbitration.py
from __future__ import annotations

from typing import List

from app.ai.models import (
    DecisionProposal,
    AgentVerdict,
    ArbitrationOutcome,
)


class ArbitrationEngine:
    """
    Combines Heimdall + Loki verdicts into a single outcome.
    Rules (you can tune later):
      - If both agree → final decision = that decision, consensus = 1.0.
      - If they disagree → default to more conservative (deny if either denies).
      - Always log notes + flags explaining what happened.
    """

    @classmethod
    def arbitrate(
        cls,
        proposal: DecisionProposal,
        primary: AgentVerdict,
        secondary: AgentVerdict,
    ) -> ArbitrationOutcome:
        notes: List[str] = []
        flags: List[str] = []

        # Agreement check
        if primary.approved == secondary.approved:
            final_approved = primary.approved
            consensus = 1.0
            notes.append(
                f"Agents agree on decision: {final_approved} "
                f"({primary.agent_name}, {secondary.agent_name})."
            )
        else:
            # Disagreement → choose more conservative route
            final_approved = primary.approved and secondary.approved
            consensus = 0.5
            flags.append("agents_disagree")
            notes.append(
                f"Agents disagree: "
                f"{primary.agent_name} approved={primary.approved} "
                f"vs {secondary.agent_name} approved={secondary.approved}."
            )
            if not final_approved:
                notes.append(
                    "Conservative policy applied: denial favored when disagreement occurs."
                )

        return ArbitrationOutcome(
            decision_id=proposal.id,
            domain=proposal.domain,
            final_approved=final_approved,
            consensus=consensus,
            primary_agent=primary.agent_name,
            secondary_agent=secondary.agent_name,
            notes=notes,
            flags=flags,
            raw={
                "proposal": proposal.dict(),
                "primary": primary.dict(),
                "secondary": secondary.dict(),
            },
        )
