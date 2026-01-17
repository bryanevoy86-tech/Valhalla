"""
PACK AO: Explainability Engine Service
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.explanation_logs import ExplanationLog
from app.schemas.explanation_engine import ExplanationRequest


EXPLANATION_TEMPLATES = {
    "scorecard": "Scorecard for {{context_id}} was generated using {{metric_count}} metrics. Key factors: {{keys}}.",
    "audit_event": "Audit event {{context_id}} was triggered because {{reason}}.",
    "decision": "Decision {{context_id}} was made based on {{criteria}}.",
}


def generate_explanation_text(context_type: str, payload: Dict[str, Any]) -> str:
    """Generate human-readable explanation from template and payload."""
    template = EXPLANATION_TEMPLATES.get(
        context_type,
        "Explanation for {{context_type}} generated.",
    )
    text = template
    for k, v in payload.items():
        text = text.replace(f"{{{{{k}}}}}", str(v))
    return text


def create_explanation(db: Session, payload: ExplanationRequest) -> ExplanationLog:
    """Create an explanation log entry."""
    expl = generate_explanation_text(payload.context_type, payload.payload)

    log = ExplanationLog(
        context_type=payload.context_type,
        context_id=payload.context_id,
        explanation=expl,
        metadata=payload.payload,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
