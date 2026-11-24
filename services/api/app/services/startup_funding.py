"""Dated owner intake and eligibility drafts against the existing grant catalog."""
from datetime import date, timedelta
from typing import Literal

from fastapi import HTTPException
from pydantic import Field, HttpUrl, model_validator
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session, lazyload

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.models.grants import GrantRecord, GrantSource
from app.schemas.market_intelligence import StrictModel
from app.services.prime_business_execution import _event, _json
from app.services.wealth_scenario import Minor


EVENT = "STARTUP_FUNDING_SOURCE_OBSERVED"


class FundingSourceIn(StrictModel):
    grant_id: int = Field(strict=True, gt=0)
    source_url: HttpUrl
    observed_on: date
    valid_through: date
    kind: Literal["GRANT", "REIMBURSEMENT", "TECHNOLOGY_CREDIT", "LOAN", "SUBSIDY"]
    currency: Literal["CAD", "USD", "GBP", "EUR"]
    maximum_minor: Minor
    minimum_match_minor: Minor
    permits_unregistered: bool
    prior_spend_rule: Literal["PROHIBITED", "PERMITTED", "UNKNOWN"]
    eligibility_requirements: list[str] = Field(min_length=1, max_length=12)
    conditions: str = Field(min_length=3, max_length=1600)

    @model_validator(mode="after")
    def source_is_bounded(self):
        if (self.source_url.scheme != "https" or self.source_url.username or self.source_url.password
                or self.source_url.query or self.source_url.fragment
                or not self.observed_on <= self.valid_through <= self.observed_on + timedelta(days=90)):
            raise ValueError("Use a dated HTTPS source without credentials or tracking parameters")
        if any(not 3 <= len(rule.strip()) <= 250 for rule in self.eligibility_requirements):
            raise ValueError("Eligibility requirements must be concise")
        return self


class FundingReviewIn(StrictModel):
    grant_id: int = Field(strict=True, gt=0)
    registration_date: date | None = None
    intended_spend_date: date | None = None
    available_matching_cad_minor: Minor


def _catalog(db: Session, grant_id: int, *, lock: bool = False):
    inspector = inspect(db.connection())
    if not all(inspector.has_table(model.__tablename__) for model in (GrantRecord, GrantSource, LegacyOrchestrationEvent)):
        raise HTTPException(503, "Funding evidence storage unavailable")
    statement = select(GrantRecord).options(lazyload(GrantRecord.source)).where(GrantRecord.id == grant_id)
    grant = db.scalar(statement.with_for_update() if lock else statement)
    source = db.get(GrantSource, grant.source_id) if grant is not None and grant.source_id else None
    if grant is None or source is None or not source.active or not grant.link:
        raise HTTPException(409, "An active catalog source with a program link is required")
    catalog = {"grant_id": grant.id, "source_id": source.id, "program_title": grant.title, "registered_source_url": source.url,
               "program_url": grant.link, "jurisdiction": grant.region or source.region,
               "deadline": grant.deadline.isoformat() if grant.deadline else None}
    return catalog


def _latest(db: Session, grant_id: int, owner_id: int):
    prefix = f"FUND-{owner_id}-{grant_id}-"
    row = db.scalar(select(LegacyOrchestrationEvent).where(
        LegacyOrchestrationEvent.event_type == EVENT,
        LegacyOrchestrationEvent.event_id.startswith(prefix),
    ).order_by(LegacyOrchestrationEvent.id.desc()).limit(1))
    if row is None:
        return None
    data = _json(row.payload_json, {})
    if not isinstance(data, dict):
        raise HTTPException(409, "Funding observation failed integrity")
    digest = artifact_digest("startup_funding_observation", prefix, data)
    if row.event_id != prefix + digest[:40]:
        raise HTTPException(409, "Funding observation failed integrity")
    return {**data, "sha256": digest}


def stage_funding_source(db: Session, request: FundingSourceIn, owner_id: int, today: date):
    catalog = _catalog(db, request.grant_id, lock=True)
    if str(request.source_url).rstrip("/") != catalog["program_url"].rstrip("/") or request.observed_on > today:
        raise HTTPException(422, "Observation must match the registered program link and available dates")
    value = {"catalog": catalog, "observation": request.model_dump(mode="json"),
             "basis": "OWNER_ATTESTED_SOURCE_OBSERVATION", "independently_verified": False}
    prior = _latest(db, request.grant_id, owner_id)
    prefix = f"FUND-{owner_id}-{request.grant_id}-"
    digest = artifact_digest("startup_funding_observation", prefix, value)
    if prior is not None and prior["sha256"] == digest:
        return prior
    if prior is not None and prior["observation"]["observed_on"] >= request.observed_on.isoformat():
        raise HTTPException(409, "Changed funding observations require a later source date")
    _event(db, event_id=prefix + digest[:40], legacy_instance_id=None, event_type=EVENT,
           message="Owner-staged funding source observation", payload=value)
    db.commit()
    return {**value, "sha256": digest}


def review_funding(db: Session, request: FundingReviewIn, owner_id: int, today: date):
    catalog = _catalog(db, request.grant_id)
    reading = _latest(db, request.grant_id, owner_id)
    if reading is None:
        raise HTTPException(404, "No dated owner funding observation")
    evidence = FundingSourceIn.model_validate(reading["observation"])
    if reading["catalog"] != catalog or not evidence.observed_on <= today <= evidence.valid_through:
        raise HTTPException(409, "Funding observation is stale or the catalog has changed")
    if request.registration_date is not None and request.registration_date > today:
        raise HTTPException(422, "Registration must already have occurred")
    blockers = []
    deadline = date.fromisoformat(catalog["deadline"]) if catalog["deadline"] else None
    if deadline is None:
        blockers.append("APPLICATION_DEADLINE_UNCONFIRMED")
    elif deadline < today:
        blockers.append("APPLICATION_WINDOW_CLOSED")
    if request.registration_date is None and not evidence.permits_unregistered:
        blockers.append("REGISTRATION_REQUIRED")
    if evidence.prior_spend_rule != "PERMITTED" and request.intended_spend_date is not None:
        blockers.append("EARLY_SPEND_REQUIRES_REVIEW")
    if evidence.currency != "CAD" and evidence.minimum_match_minor:
        blockers.append("MATCHING_CAPITAL_CURRENCY_UNCHECKED")
    elif evidence.minimum_match_minor > request.available_matching_cad_minor:
        blockers.append("MATCHING_CAPITAL_SHORTFALL")
    return {
        "source": reading, "basis": "DRAFT_FUNDING_ELIGIBILITY", "blockers": blockers,
        "status": "HOLD" if blockers else "POTENTIALLY_ELIGIBLE",
        "application_preparation": {
            "status": "DRAFT_REQUIRES_REVIEW", "requirements": evidence.eligibility_requirements,
            "conditions": evidence.conditions, "verify_deadline_and_program_contact": True,
            "verify_eligible_expenditures_and_stacking": True,
        },
        "verified_eligible": False, "included_in_spendable_cash_minor": 0,
        "external_application_authorized": False,
    }
