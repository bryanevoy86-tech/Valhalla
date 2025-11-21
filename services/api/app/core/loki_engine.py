"""Loki Deep Counter-Analysis Engine (Pack 81).

Provides adversarial / counter-frame analysis utilities for a given input artifact.
This is a lightweight synchronous stub; real ML inference can replace the heuristics later.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CounterFrameResult:
    reverse_frame: str
    assumptions: List[str]
    risk_map: Dict[str, Any]
    worst_case: str
    suggested_corrections: List[str]
    confidence: float
    version: str = "1.0-shadow"
    analyzed_at: datetime = datetime.utcnow()


class LokiCounterEngine:
    """Performs counter-analysis on textual artifacts.

    Heuristic approach:
    - Reverse frame: attempt to invert the default perspective (e.g., benefits -> risks).
    - Assumptions: naive extraction by scanning for modal / assertive verbs.
    - Risk map: categorize perceived risks (operational, legal, financial, security).
    - Worst case: synthesize high-impact scenario.
    - Suggested corrections: surface mitigation statements.
    - Confidence: simple function of artifact length & diversity of detected tokens.
    """

    MODAL_HINTS = [
        "must", "will", "always", "never", "should", "cannot", "guarantee", "proven",
    ]
    RISK_CATEGORIES = {
        "operational": ["delay", "scaling", "outage", "downtime"],
        "legal": ["compliance", "regulation", "licensing", "gdpr"],
        "financial": ["cost", "expense", "loss", "revenue"],
        "security": ["breach", "vulnerability", "leak", "exploit"],
    }

    def analyze(
        self,
        artifact_text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CounterFrameResult:
        text_lower = artifact_text.lower()

        reverse_frame = self._build_reverse_frame(artifact_text)
        assumptions = self._extract_assumptions(text_lower)
        risk_map = self._build_risk_map(text_lower)
        worst_case = self._synthesize_worst_case(risk_map, artifact_text)
        suggested_corrections = self._suggest_corrections(risk_map, assumptions)
        confidence = self._estimate_confidence(artifact_text, assumptions, risk_map)

        # Allow context hints to tweak outputs (e.g., provided risk profile)
        if context and context.get("risk_profile"):
            risk_map["profile"] = context["risk_profile"]

        return CounterFrameResult(
            reverse_frame=reverse_frame,
            assumptions=assumptions,
            risk_map=risk_map,
            worst_case=worst_case,
            suggested_corrections=suggested_corrections,
            confidence=confidence,
        )

    # --- Internal helpers -------------------------------------------------

    def _build_reverse_frame(self, original: str) -> str:
        if len(original) < 20:
            return "Input too brief for meaningful reverse framing."
        return (
            "Adversarial reframing: scrutinize each claimed benefit; identify latent risks, "
            "challenge optimistic timelines, and test robustness against failure modes."
        )

    def _extract_assumptions(self, text_lower: str) -> List[str]:
        found = []
        for hint in self.MODAL_HINTS:
            if hint in text_lower:
                found.append(f"Potential hidden assumption implied by '{hint}'.")
        if not found:
            found.append("No strong modal assertion tokens detected; assumptions minimal or implicit.")
        return found[:12]

    def _build_risk_map(self, text_lower: str) -> Dict[str, Any]:
        risk_map: Dict[str, Any] = {"categories": {}, "raw_flags": []}
        for category, keywords in self.RISK_CATEGORIES.items():
            hits = [k for k in keywords if k in text_lower]
            if hits:
                risk_map["categories"][category] = {
                    "hits": hits,
                    "severity": self._categorize_severity(len(hits)),
                }
                risk_map["raw_flags"].extend(hits)
        if not risk_map["categories"]:
            risk_map["categories"] = {"general": {"hits": [], "severity": "low"}}
        return risk_map

    def _categorize_severity(self, count: int) -> str:
        if count >= 4:
            return "high"
        if count >= 2:
            return "moderate"
        return "low"

    def _synthesize_worst_case(self, risk_map: Dict[str, Any], original: str) -> str:
        flagged = risk_map.get("raw_flags", [])
        if not flagged:
            return "Worst-case scenario limited; no explicit high-risk tokens found."
        return (
            "Worst-case: cascading impact where "
            + ", ".join(flagged[:6])
            + " amplify each other, leading to systemic failure and stakeholder escalation."
        )

    def _suggest_corrections(
        self, risk_map: Dict[str, Any], assumptions: List[str]
    ) -> List[str]:
        corrections: List[str] = []
        for cat, meta in risk_map.get("categories", {}).items():
            if cat == "general":
                continue
            severity = meta.get("severity")
            corrections.append(
                f"Mitigate {cat} exposure: add monitoring + fallback; current severity {severity}."
            )
        if assumptions and "No strong modal" not in assumptions[0]:
            corrections.append(
                "Validate critical assumptions via empirical tests or pilot before full rollout."
            )
        if not corrections:
            corrections.append("No material corrections surfaced under heuristic model.")
        return corrections[:10]

    def _estimate_confidence(
        self, original: str, assumptions: List[str], risk_map: Dict[str, Any]
    ) -> float:
        base = min(len(original) / 500.0, 1.0)  # length heuristic
        diversity = len(risk_map.get("categories", {})) / 6.0
        assumption_factor = 0.7 if assumptions and "No strong modal" not in assumptions[0] else 0.4
        score = (base * 0.5) + (diversity * 0.3) + (assumption_factor * 0.2)
        return round(min(max(score, 0.05), 0.98), 3)


engine = LokiCounterEngine()
