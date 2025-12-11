"""
PACK AD: SaaS Access Engine Service
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.saas_access import SaaSPlan, SaaSPlanModule, Subscription
from app.schemas.saas_access import SaaSPlanCreate, SaaSPlanUpdate, SubscriptionCreate, SubscriptionUpdate


def create_plan(db: Session, payload: SaaSPlanCreate) -> SaaSPlan:
    plan = SaaSPlan(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        price_monthly=payload.price_monthly,
        price_yearly=payload.price_yearly,
        currency=payload.currency,
    )
    db.add(plan)
    db.flush()  # so plan.id is available

    for mod in payload.modules:
        db.add(SaaSPlanModule(plan_id=plan.id, module_key=mod.module_key))

    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db: Session, plan_id: int, payload: SaaSPlanUpdate) -> Optional[SaaSPlan]:
    plan = db.query(SaaSPlan).filter(SaaSPlan.id == plan_id).first()
    if not plan:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan


def list_plans(db: Session) -> List[SaaSPlan]:
    return db.query(SaaSPlan).filter(SaaSPlan.is_active.is_(True)).all()


def get_plan(db: Session, plan_id: int) -> Optional[SaaSPlan]:
    return db.query(SaaSPlan).filter(SaaSPlan.id == plan_id).first()


def create_subscription(db: Session, payload: SubscriptionCreate) -> Subscription:
    sub = Subscription(**payload.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def update_subscription(
    db: Session,
    subscription_id: int,
    payload: SubscriptionUpdate,
) -> Optional[Subscription]:
    sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not sub:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(sub, field, value)

    # set cancelled_at when status goes to cancelled
    if sub.status == "cancelled" and sub.cancelled_at is None:
        sub.cancelled_at = datetime.utcnow()

    db.commit()
    db.refresh(sub)
    return sub


def get_active_subscription_for_user(db: Session, user_id: int) -> Optional[Subscription]:
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id, Subscription.status == "active")
        .order_by(Subscription.started_at.desc())
        .first()
    )


def get_modules_for_plan(db: Session, plan_id: int) -> List[SaaSPlanModule]:
    return db.query(SaaSPlanModule).filter(SaaSPlanModule.plan_id == plan_id).all()


def user_has_access(db: Session, user_id: int, module_key: str) -> tuple[bool, Optional[str]]:
    sub = get_active_subscription_for_user(db, user_id)
    if not sub:
        return False, None

    mods = get_modules_for_plan(db, sub.plan_id)
    keys = {m.module_key for m in mods}
    return module_key in keys, sub.plan.code if sub.plan else None
