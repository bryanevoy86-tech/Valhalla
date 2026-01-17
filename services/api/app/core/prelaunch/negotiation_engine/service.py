"""Negotiation Engine Service Layer"""
from sqlalchemy.orm import Session
from . import models, schemas


def pick_template(db: Session, category: str, tone: str | None):
    """Pick a negotiation template by category and optional tone."""
    q = db.query(models.NegotiationTemplate).filter(
        models.NegotiationTemplate.category == category
    )
    if tone:
        q = q.filter(models.NegotiationTemplate.tone_profile == tone)
    return q.first()


def run_negotiation(
    db: Session, payload: schemas.NegotiationRequest
) -> schemas.NegotiationResponse:
    """
    Execute a negotiation using templates and saved scripts.
    
    Later will integrate with Heimdall-generated text and style matching
    from preference_engine + behavior_engine.
    """
    template = pick_template(db, payload.category, payload.tone_profile)

    if not template:
        return schemas.NegotiationResponse(
            output="No negotiation template found for this category.",
            style_used="default",
        )

    # Simple script rendering → later replaced with Heimdall-generated text
    script_lines = []
    for step in template.script.get("steps", []):
        text = step.get("text", "")
        script_lines.append(text)

    output = "\n".join(script_lines)

    # Save session
    session = models.NegotiationSession(
        target_name=payload.target_name,
        category=payload.category,
        style_used=template.tone_profile,
        script_output=output,
    )
    db.add(session)
    db.commit()

    return schemas.NegotiationResponse(
        output=output,
        style_used=template.tone_profile,
    )
