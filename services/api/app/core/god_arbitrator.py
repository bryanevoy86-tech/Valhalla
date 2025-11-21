"""Dual-God Arbitration Engine (Pack 82).

Combines Heimdall and Loki stance summaries (and optional dispute / verdict signals)
into a synthesized recommendation with merged risk tier & confidence.
Heuristic stub; replace with more robust ensemble / model logic later.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ArbitrationResult:
    final_recommendation: str
    merged_risk_tier: str
    consensus: str
    confidence: float
    reasoning: Dict[str, Any]
    version: str = "1.0-arbiter"
    decided_at: datetime = datetime.utcnow()


class GodArbitrator:
    """Synthesizes multi-perspective outputs.

    Heuristic strategy:
    - Risk tier merge: pick the higher (more severe) between Heimdall & Loki.
    - Consensus: align if recommendation keywords overlap; else "divergent".
    - Confidence: base on overlap + difference in risk (bigger difference lowers confidence).
    - Final recommendation: if divergent, prefer more conservative stance with appended note.
    """

    POSITIVE_TOKENS = {"approve", "proceed", "go", "ship"}
    CAUTION_TOKENS = {"hold", "block", "review", "revise", "delay"}

    def arbitrate(
        self,
        heimdall_summary: str,
        loki_summary: str,
        heimdall_risk_tier: str,
        loki_risk_tier: str,
        dispute_context: Optional[Dict[str, Any]] = None,
        verdict_context: Optional[Dict[str, Any]] = None,
    ) -> ArbitrationResult:
        tokens_heimdall = set(heimdall_summary.lower().split())
        tokens_loki = set(loki_summary.lower().split())
        overlap = tokens_heimdall.intersection(tokens_loki)

        merged_risk = self._merge_risk(heimdall_risk_tier, loki_risk_tier)
        consensus = "aligned" if self._is_consensus(overlap) else "divergent"
        confidence = self._compute_confidence(overlap, heimdall_risk_tier, loki_risk_tier)

        final = self._compose_final_recommendation(
            heimdall_summary,
            loki_summary,
            consensus,
            merged_risk,
        )

        reasoning = {
            "overlap_tokens": sorted(list(overlap))[:30],
            "heimdall_risk_tier": heimdall_risk_tier,
            "loki_risk_tier": loki_risk_tier,
            "merged_logic": "select-higher-tier",
            "consensus_logic": "token-overlap + polarity heuristic",
        }
        if dispute_context:
            reasoning["dispute_ref"] = dispute_context.get("id")
        if verdict_context:
            reasoning["verdict_ref"] = verdict_context.get("id")

        return ArbitrationResult(
            final_recommendation=final,
            merged_risk_tier=merged_risk,
            consensus=consensus,
            confidence=confidence,
            reasoning=reasoning,
        )

    # --- Helpers ----------------------------------------------------------

    def _merge_risk(self, heimdall: str, loki: str) -> str:
        order = ["low", "moderate", "elevated", "high", "critical"]
        try:
            idx_h = order.index(heimdall.lower())
            idx_l = order.index(loki.lower())
        except ValueError:
            return loki or heimdall or "unknown"
        return order[max(idx_h, idx_l)]

    def _is_consensus(self, overlap: set[str]) -> bool:
        if len(overlap) >= 5:
            return True
        return False

    def _compute_confidence(
        self, overlap: set[str], heimdall_risk: str, loki_risk: str
    ) -> float:
        base = min(len(overlap) / 25.0, 0.85)
        spread_penalty = 0.0 if heimdall_risk == loki_risk else 0.15
        score = base + 0.1 - spread_penalty
        return round(min(max(score, 0.05), 0.95), 3)

    def _compose_final_recommendation(
        self, heimdall_summary: str, loki_summary: str, consensus: str, merged_risk: str
    ) -> str:
        if consensus == "aligned":
            return f"Proceed with caution; merged risk {merged_risk}. Unified perspective."[:300]
        # Divergent: pick conservative tone
        polarity_h = self._polarity(heimdall_summary)
        polarity_l = self._polarity(loki_summary)
        conservative_source = (
            "Heimdall" if polarity_h <= polarity_l else "Loki"
        )  # lower polarity => more conservative
        return (
            f"Divergent views; adopt {conservative_source} conservative stance. Merged risk {merged_risk}. "
            "Initiate focused review to reconcile key disagreements."[:300]
        )

    def _polarity(self, text: str) -> int:
        tl = text.lower()
        pos = sum(1 for t in self.POSITIVE_TOKENS if t in tl)
        neg = sum(1 for t in self.CAUTION_TOKENS if t in tl)
        return pos - neg


arbiter = GodArbitrator()
