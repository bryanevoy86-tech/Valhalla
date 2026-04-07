# services/api/app/routers/pro_behavioral_extract.py

from __future__ import annotations

import httpx
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status

from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/pros",
    tags=["Professionals", "BehavioralSignals"],
)


# ------------------------------
# SCHEMAS
# ------------------------------

class PublicSource(BaseModel):
    url: str = Field(..., description="Publicly accessible URL to scan for text.")
    category: str = Field(
        default="general",
        description="Optional tag: bio, services, reviews, about, articles, etc."
    )


class ExtractRequest(BaseModel):
    name: str = Field(..., description="Name of the professional or firm.")
    sources: List[PublicSource] = Field(
        ..., description="List of public URLs to scan for text."
    )


class BehavioralSignals(BaseModel):
    """
    SAFE behavioral signals derived from PUBLIC data ONLY.
    No psychology. No diagnosis. No personal judgments.
    Only neutral text-derived indicators.
    """

    communication_clarity: Optional[float] = Field(
        None,
        description="0–1 measure of clarity based on sentence structure & complexity.",
    )
    professionalism_tone: Optional[float] = Field(
        None,
        description="0–1 measure of formal/professional tone in written content.",
    )
    transparency_level: Optional[float] = Field(
        None,
        description="0–1 score based on presence of concrete details vs vague statements.",
    )
    response_expectation: Optional[str] = Field(
        None,
        description="Expected response speed if publicly advertised (e.g., '24h', '48h').",
    )
    service_specialization: List[str] = Field(
        default_factory=list,
        description="Detected areas of service specialty."
    )
    risk_style: Optional[str] = Field(
        None,
        description="Surface-level indicator: conservative / balanced / aggressive based on wording."
    )


class ExtractResponse(BaseModel):
    name: str
    signals: BehavioralSignals
    raw_text: str = Field("", description="Optional extracted text for debugging.")
    sources_scanned: int


# ------------------------------
# UTILITY FUNCTIONS
# ------------------------------

async def fetch_text(url: str) -> str:
    """Fetch text content from a PUBLIC web page."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        return f""


def extract_clarity(text: str) -> float:
    """Very simple clarity heuristic: shorter sentences = clearer tone."""
    if not text:
        return 0.0
    sentences = text.split(".")
    avg_len = sum(len(s.split()) for s in sentences if s.strip()) / max(1, len(sentences))
    # Invert complexity: shorter sentences → higher clarity
    clarity = max(0.0, min(1.0, 1 - (avg_len / 40)))
    return round(clarity, 2)


def extract_professionalism(text: str) -> float:
    """Looks for presence of formal vocabulary."""
    if not text:
        return 0.0
    keywords = ["professional", "expert", "licensed", "experience", "certified", "practice"]
    score = sum(1 for word in keywords if word.lower() in text.lower()) / len(keywords)
    return round(min(1.0, score), 2)


def extract_transparency(text: str) -> float:
    """Measures use of numbers, details, credentials—indicating transparency."""
    import re
    if not text:
        return 0.0
    numbers = len(re.findall(r"\d+", text))
    details = len([w for w in text.split() if len(w) > 6])
    transparency = min(1.0, (numbers + details / 10) / 10)
    return round(transparency, 2)


def extract_specialization(text: str) -> List[str]:
    keywords = {
        "real estate": ["real estate", "property", "title", "closing"],
        "corporate": ["corporate", "business", "entity", "incorporation"],
    }
    found = []
    for label, words in keywords.items():
        if any(w in text.lower() for w in words):
            found.append(label)
    return found


def extract_risk_style(text: str) -> str:
    """Simple lexical marker (not psychological): aggressive wording vs cautious wording."""
    t = text.lower()
    aggressive = ["dominate", "guarantee", "win", "force", "aggressive"]
    conservative = ["careful", "thorough", "risk management", "caution"]

    if any(a in t for a in aggressive):
        return "aggressive"
    if any(c in t for c in conservative):
        return "conservative"
    return "balanced"


# ------------------------------
# ROUTE
# ------------------------------

@router.post(
    "/extract_signals",
    response_model=ExtractResponse,
    summary="Extract safe behavioral signals from PUBLIC information",
    description="Scans public URLs for pattern-based signals (clarity, tone, transparency, specialization, risk style)."
)
async def extract_behavior_signals(payload: ExtractRequest):
    all_text = ""

    # Fetch all public sources
    for src in payload.sources:
        text = await fetch_text(src.url)
        if text:
            all_text += "\n" + text

    if not all_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No public text could be extracted from the provided sources."
        )

    # Build SAFE, NON-PSYCHOLOGICAL signals
    signals = BehavioralSignals(
        communication_clarity=extract_clarity(all_text),
        professionalism_tone=extract_professionalism(all_text),
        transparency_level=extract_transparency(all_text),
        response_expectation="unknown",
        service_specialization=extract_specialization(all_text),
        risk_style=extract_risk_style(all_text),
    )

    return ExtractResponse(
        name=payload.name,
        signals=signals,
        raw_text=all_text[:5000],  # For debugging only, truncated
        sources_scanned=len(payload.sources),
    )
