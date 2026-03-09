from __future__ import annotations

from fastapi import APIRouter, HTTPException
from typing import Optional

from .schemas import JurisdictionProfileUpsert, ProfileListResponse, LegalCheckRequest, LegalCheckResponse
from . import service

router = APIRouter(prefix="/core/legal", tags=["core-legal"])


@router.post("/profiles")
def upsert_profile(payload: JurisdictionProfileUpsert):
    try:
        return service.upsert_profile(payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profiles", response_model=ProfileListResponse)
def list_profiles():
    return {"items": service.list_profiles()}


@router.get("/profiles/{key}")
def get_profile(key: str):
    p = service.get_profile(key)
    if not p:
        raise HTTPException(status_code=404, detail="profile not found")
    return p


@router.post("/seed_defaults")
def seed_defaults():
    return service.seed_defaults_if_empty()


@router.post("/check", response_model=LegalCheckResponse)
def check(payload: LegalCheckRequest):
    try:
        return service.run_check(
            jurisdiction_key=payload.jurisdiction_key,
            subject=payload.subject,
            payload=payload.payload,
            mode=payload.mode,
            cone_band=payload.cone_band,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="jurisdiction profile not found")
