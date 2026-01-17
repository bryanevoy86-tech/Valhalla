"""
PACK AD: SaaS Access Engine Router
Prefix: /saas
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.saas_access import (
    SaaSPlanCreate,
    SaaSPlanUpdate,
    SaaSPlanOut,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionOut,
    AccessCheckOut,
)
from app.services.saas_access import (
    create_plan,
    update_plan,
    list_plans,
    get_plan,
    create_subscription,
    update_subscription,
    get_active_subscription_for_user,
    user_has_access,
)

router = APIRouter(prefix="/saas", tags=["SaaS"])


@router.post("/plans", response_model=SaaSPlanOut)
def create_plan_endpoint(
    payload: SaaSPlanCreate,
    db: Session = Depends(get_db),
):
    """Create a new SaaS plan with optional modules"""
    return create_plan(db, payload)


@router.get("/plans", response_model=List[SaaSPlanOut])
def list_plans_endpoint(db: Session = Depends(get_db)):
    """List all active SaaS plans"""
    return list_plans(db)


@router.get("/plans/{plan_id}", response_model=SaaSPlanOut)
def get_plan_endpoint(
    plan_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific SaaS plan by ID"""
    plan = get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.patch("/plans/{plan_id}", response_model=SaaSPlanOut)
def update_plan_endpoint(
    plan_id: int,
    payload: SaaSPlanUpdate,
    db: Session = Depends(get_db),
):
    """Update a SaaS plan"""
    plan = update_plan(db, plan_id, payload)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/subscriptions", response_model=SubscriptionOut)
def create_subscription_endpoint(
    payload: SubscriptionCreate,
    db: Session = Depends(get_db),
):
    """Create a new subscription for a user"""
    return create_subscription(db, payload)


@router.patch("/subscriptions/{subscription_id}", response_model=SubscriptionOut)
def update_subscription_endpoint(
    subscription_id: int,
    payload: SubscriptionUpdate,
    db: Session = Depends(get_db),
):
    """Update a subscription (status, provider_sub_id, etc.)"""
    sub = update_subscription(db, subscription_id, payload)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.get("/subscriptions/active/{user_id}", response_model=Optional[SubscriptionOut])
def get_active_subscription_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Get the active subscription for a user"""
    return get_active_subscription_for_user(db, user_id)


@router.get("/access-check", response_model=AccessCheckOut)
def access_check_endpoint(
    user_id: int = Query(...),
    module_key: str = Query(...),
    db: Session = Depends(get_db),
):
    """Check if a user has access to a specific module"""
    has_access, plan_code = user_has_access(db, user_id, module_key)
    return AccessCheckOut(
        user_id=user_id,
        module_key=module_key,
        has_access=has_access,
        plan_code=plan_code,
    )
