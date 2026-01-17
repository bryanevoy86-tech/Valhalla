# services/api/app/routers/pro_alignment_engine.py

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

from app.routers.pro_behavioral_extract import BehavioralSignals

router = APIRouter(
    prefix="/pros",
    tags=["Professionals", "Alignment"],
)

# --------------------------------------------
# IDEAL VALHALLA OPERATIONAL PROFILE
# --------------------------------------------

class IdealBehaviorProfile(BaseModel):
    """
    This represents Valhalla's desired working-style alignment.
    Not psychological. Not personal. Strictly operational and behavioral.
    """

    target_clarity: float = Field(0.7)
    target_professionalism: float = Field(0.7)
    target_transparency: float = Field(0.6)

    # Allowed values: conservative / balanced / aggressive
    preferred_risk_style: str = Field(
        "balanced",
        description="General risk orientation preferred for Valhalla operations.",
    )

    preferred_specializations: List[str] = Field(
        default_factory=lambda: ["real estate", "corporate"]
    )


class AlignmentRequest(BaseModel):
    name: str
    signals: BehavioralSignals
    ideal: IdealBehaviorProfile = IdealBehaviorProfile()


class AlignmentScores(BaseModel):
    clarity_score: float
    professionalism_score: float
    transparency_score: float
    specialization_score: float
    risk_style_score: float
    overall_score: float


class AlignmentSummary(BaseModel):
    strengths: List[str]
    risks: List[str]
    recommendation: str


class AlignmentResponse(BaseModel):
    name: str
    scores: AlignmentScores
    summary: AlignmentSummary
    matched_specializations: List[str]
    raw_signals: BehavioralSignals


# --------------------------------------------
# SCORING LOGIC
# --------------------------------------------

def score_clarity(actual: float, target: float) -> float:
    if actual is None:
        return 0.0
    return round(min(1.0, actual / max(0.01, target)), 2)


def score_professionalism(actual: float, target: float) -> float:
    if actual is None:
        return 0.0
    return round(min(1.0, actual / max(0.01, target)), 2)


def score_transparency(actual: float, target: float) -> float:
    if actual is None:
        return 0.0
    return round(min(1.0, actual / max(0.01, target)), 2)


def score_specializations(found: List[str], preferred: List[str]) -> float:
    if not found:
        return 0.0
    overlap = len([x for x in found if x in preferred])
    return round(overlap / len(preferred), 2)


def score_risk_style(actual: str, preferred: str) -> float:
    if not actual:
        return 0.0
    if actual == preferred:
        return 1.0
    if preferred == "balanced":
        return 0.7  # slight penalty
    return 0.5  # mismatch score


# --------------------------------------------
# SUMMARY LOGIC
# --------------------------------------------

def build_summary(scores: AlignmentScores) -> AlignmentSummary:
    strengths = []
    risks = []

    if scores.clarity_score > 0.7:
        strengths.append("Clear communication style.")
    else:
        risks.append("Communication may require clarification or structure.")

    if scores.professionalism_score > 0.7:
        strengths.append("Consistent professional tone.")
    else:
        risks.append("Tone suggests potential inconsistency or informality.")

    if scores.transparency_score > 0.6:
        strengths.append("Provides detailed and concrete information publicly.")
    else:
        risks.append("Limited transparency in publicly available information.")

    if scores.specialization_score > 0.5:
        strengths.append("Relevant specialization detected for Valhalla operations.")
    else:
        risks.append("Specialization does not strongly align with required domains.")

    if scores.risk_style_score >= 0.9:
        strengths.append("Risk style matches Valhalla preferences.")
    elif scores.risk_style_score < 0.5:
        risks.append("Risk style may not align with Valhalla's operational approach.")

    # Recommendation logic
    if scores.overall_score >= 0.75:
        recommendation = "Strong candidate for further engagement."
    elif scores.overall_score >= 0.55:
        recommendation = "Potential candidate; recommended for interview."
    else:
        recommendation = "Low alignment; review other candidates."

    return AlignmentSummary(
        strengths=strengths,
        risks=risks,
        recommendation=recommendation,
    )


# --------------------------------------------
# ROUTER
# --------------------------------------------

@router.post(
    "/align_profile",
    response_model=AlignmentResponse,
    summary="Compare public behavioral signals to Valhalla's ideal profile.",
    description="Produces a SAFE, NON-PSYCHOLOGICAL alignment score for professional compatibility.",
)
def align_profile(req: AlignmentRequest):

    if not req.signals:
        raise HTTPException(
            status_code=422,
            detail="Behavioral signals missing. Extract signals first."
        )

    # Scoring
    clarity = score_clarity(req.signals.communication_clarity, req.ideal.target_clarity)
    professionalism = score_professionalism(req.signals.professionalism_tone, req.ideal.target_professionalism)
    transparency = score_transparency(req.signals.transparency_level, req.ideal.target_transparency)
    specialization = score_specializations(req.signals.service_specialization, req.ideal.preferred_specializations)
    risk_style = score_risk_style(req.signals.risk_style, req.ideal.preferred_risk_style)

    overall = round(
        (clarity + professionalism + transparency + specialization + risk_style) / 5, 2
    )

    scores = AlignmentScores(
        clarity_score=clarity,
        professionalism_score=professionalism,
        transparency_score=transparency,
        specialization_score=specialization,
        risk_style_score=risk_style,
        overall_score=overall,
    )

    summary = build_summary(scores)

    return AlignmentResponse(
        name=req.name,
        scores=scores,
        summary=summary,
        matched_specializations=req.signals.service_specialization,
        raw_signals=req.signals,
    )
