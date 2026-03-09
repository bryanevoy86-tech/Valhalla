"""
PACK AX: Feature Flags & Experiments Router
Prefix: /features
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.feature_flags import (
    FeatureFlagCreate,
    FeatureFlagUpdate,
    FeatureFlagOut,
)
from app.services.feature_flags import (
    create_feature_flag,
    update_feature_flag,
    get_flag_by_key,
    list_feature_flags,
)

router = APIRouter(prefix="/features", tags=["FeatureFlags"])


@router.post("/", response_model=FeatureFlagOut)
def create_feature_flag_endpoint(
    payload: FeatureFlagCreate,
    db: Session = Depends(get_db),
):
    """Create a new feature flag."""
    return create_feature_flag(db, payload)


@router.patch("/{flag_id}", response_model=FeatureFlagOut)
def update_feature_flag_endpoint(
    flag_id: int,
    payload: FeatureFlagUpdate,
    db: Session = Depends(get_db),
):
    """Update a feature flag."""
    obj = update_feature_flag(db, flag_id, payload)
    if not obj:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return obj


@router.get("/", response_model=List[FeatureFlagOut])
def list_feature_flags_endpoint(
    audience: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List feature flags with optional audience filter."""
    return list_feature_flags(db, audience=audience)


@router.get("/{key}", response_model=FeatureFlagOut)
def get_feature_flag_by_key_endpoint(
    key: str,
    db: Session = Depends(get_db),
):
    """Get feature flag by key."""
    obj = get_flag_by_key(db, key)
    if not obj:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return obj
