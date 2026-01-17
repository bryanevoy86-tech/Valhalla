from __future__ import annotations

from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    JurisdictionProfile,
    LegalRule,
    RuleCondition,
    EvaluateResponse,
    JurisdictionListResponse,
    RuleListResponse,
)
from . import service

router = APIRouter(prefix="/legal", tags=["core-legal"])


@router.get("/profiles", response_model=JurisdictionListResponse)
def list_profiles(country: Optional[str] = Query(default=None), region: Optional[str] = Query(default=None)):
    items = service.list_profiles_filtered(country=country, region=region)
    return {"items": items}


@router.post("/profiles", response_model=JurisdictionProfile)
def create_profile(country: str, region: str, name: str, notes: str = ""):
    rec = service.create_profile(country=country, region=region, name=name, notes=notes)
    return rec


@router.get("/rules", response_model=RuleListResponse)
def list_rules(country: Optional[str] = Query(default=None), region: Optional[str] = Query(default=None)):
    items = service.list_rules_filtered(country=country, region=region)
    return {"items": items}


@router.post("/rules", response_model=LegalRule)
def create_rule(name: str, description: str = "", country: str = "CA", region: str = "ON", severity: str = "info", action_hint: str = "", conditions: Optional[list] = None):
    conds = conditions or []
    rec = service.create_rule(name=name, description=description, country=country, region=region, severity=severity, conditions=conds, action_hint=action_hint)
    return rec


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(payload: dict[str, Any], country: Optional[str] = Query(default=None), region: Optional[str] = Query(default=None)):
    result = service.evaluate(payload, country=country, region=region)
    return result
