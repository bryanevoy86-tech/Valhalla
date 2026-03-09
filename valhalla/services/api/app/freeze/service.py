from sqlalchemy.orm import Session
from typing import List
from app.freeze.models import FreezeRule, FreezeEvent
from app.freeze.schemas import FreezeRuleCreate


def create_rule(db: Session, payload: FreezeRuleCreate) -> FreezeRule:
    rule = FreezeRule(**payload.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_rules(db: Session) -> List[FreezeRule]:
    return db.query(FreezeRule).all()


def _compare(value: float, comparator: str, threshold: float) -> bool:
    if comparator == ">":
        return value > threshold
    if comparator == "<":
        return value < threshold
    if comparator == ">=":
        return value >= threshold
    if comparator == "<=":
        return value <= threshold
    return False


def evaluate_metric(db: Session, metric: str, value: float) -> FreezeEvent | None:
    active_rules = db.query(FreezeRule).filter(
        FreezeRule.metric == metric, FreezeRule.active.is_(True)
    ).all()
    for rule in active_rules:
        if _compare(value, rule.comparator or ">", rule.threshold):
            evt = FreezeEvent(
                rule_name=rule.name,
                triggered_value=value,
                message=f"Rule {rule.name} triggered on {metric}={value} {rule.comparator} {rule.threshold}",
            )
            db.add(evt)
            db.commit()
            db.refresh(evt)
            return evt
    return None


def list_events(db: Session, unresolved_only: bool = False):
    q = db.query(FreezeEvent)
    if unresolved_only:
        q = q.filter(FreezeEvent.resolved.is_(False))
    return q.order_by(FreezeEvent.id.desc()).limit(200).all()


def resolve_event(db: Session, event_id: int) -> FreezeEvent | None:
    evt = db.get(FreezeEvent, event_id)
    if not evt:
        return None
    evt.resolved = True
    db.commit()
    db.refresh(evt)
    return evt
