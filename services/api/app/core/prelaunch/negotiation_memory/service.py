"""Negotiation Memory Service Layer"""
from collections import defaultdict
from typing import List

from sqlalchemy.orm import Session

from . import models, schemas


def record_outcome(
    db: Session, data: schemas.NegotiationOutcomeCreate
) -> models.NegotiationOutcome:
    """Record a negotiation outcome."""
    o = models.NegotiationOutcome(**data.model_dump())
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


def compute_stats(db: Session) -> List[schemas.NegotiationStats]:
    """Compute negotiation statistics by category and style."""
    rows = db.query(models.NegotiationOutcome).all()
    buckets = defaultdict(list)

    for r in rows:
        key = (r.category, r.style_used)
        buckets[key].append(r)

    stats: list[schemas.NegotiationStats] = []

    for (category, style), values in buckets.items():
        total = len(values)
        wins = sum(1 for v in values if v.outcome.upper() == "WON")
        losses = sum(1 for v in values if v.outcome.upper() == "LOST")
        win_rate = wins / total if total else 0.0
        stats.append(
            schemas.NegotiationStats(
                category=category,
                style_used=style,
                total=total,
                wins=wins,
                losses=losses,
                win_rate=win_rate,
            )
        )

    return stats
