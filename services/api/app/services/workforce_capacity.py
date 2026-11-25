"""Time-bounded synthetic crew holds in the existing, digest-bound planning journal."""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import AwareDatetime, Field, model_validator
from sqlalchemy import select

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.prime_business_execution import _event, _json

RESERVE = "WORKFORCE_CAPACITY_RESERVED"
RELEASE = "WORKFORCE_CAPACITY_RELEASED"
LEASE = timedelta(minutes=30)
FixtureIdentity = Annotated[str, Field(pattern=r"^fixture:[a-z0-9-]{3,64}$")]
Minutes = Annotated[int, Field(strict=True, ge=0, le=1440)]


class Availability(StrictModel):
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode="after")
    def valid_interval(self):
        if (self.starts_at >= self.ends_at or self.starts_at.utcoffset() != timedelta(0)
                or self.ends_at.utcoffset() != timedelta(0)):
            raise ValueError("Use an ordered, UTC working interval")
        return self


class WorkWindow(Availability):
    travel_minutes: Minutes
    delay_minutes: Minutes

    @model_validator(mode="after")
    def bounded_window(self):
        if self.ends_at - self.starts_at > timedelta(days=30):
            raise ValueError("A planning window cannot exceed 30 days")
        return self

    @property
    def occupied_from(self):
        return self.starts_at - timedelta(minutes=self.travel_minutes)

    @property
    def occupied_until(self):
        return self.ends_at + timedelta(minutes=self.delay_minutes)


class VerifiedCapacity(StrictModel):
    issuer: FixtureIdentity
    human_reviewer: FixtureIdentity
    checked_at: AwareDatetime
    expires_at: AwareDatetime
    verification: Literal["VERIFIED_IN_FIXTURE", "UNVERIFIED", "WITHDRAWN"]
    privacy_basis: Literal["SYNTHETIC_NO_PERSONAL_DATA"]
    availability: list[Availability] = Field(max_length=32)
    existing_assignments: list[Availability] = Field(default_factory=list, max_length=32)

    @model_validator(mode="after")
    def verified_period(self):
        if self.issuer == self.human_reviewer or not self.checked_at < self.expires_at <= self.checked_at + timedelta(days=90):
            raise ValueError("Use distinct fixture identities and a bounded verification period")
        return self


class CapacityRequest(StrictModel):
    id: UUID
    scope: MarketScope
    opportunity_key: str = Field(pattern=r"^[a-z][a-z0-9_-]{2,79}$")


class ReviewedCapacity(CapacityRequest):
    independent_review_id: UUID
    expected_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReleaseCapacity(StrictModel):
    scope: MarketScope


def now():
    return datetime.now(timezone.utc)


def receipt_key(kind, identifier):
    return ("CREW-" if kind == RESERVE else "CREW-RELEASE-") + str(identifier)


def verified_record(row, kind):
    key = row.event_id
    payload = _json(row.payload_json, None)
    try:
        body = {name: value for name, value in payload.items() if name != "sha256"}
        if (row.event_type != kind or key != receipt_key(kind, body["reservation_id"])
                or row.legacy_instance_id != body["scope"]["legacy_instance_id"]
                or payload["sha256"] != artifact_digest(kind, key, body)):
            raise ValueError
    except (AttributeError, KeyError, TypeError, ValueError):
        raise HTTPException(409, "Capacity journal failed integrity verification") from None
    return payload


def receipt(db, kind, identifier):
    row = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=receipt_key(kind, identifier)))
    return verified_record(row, kind) if row else None


def store(db, kind, identifier, scope, **details):
    key = receipt_key(kind, identifier)
    body = {"reservation_id": str(identifier), "scope": scope, **details, "external_authority": False}
    payload = {**body, "sha256": artifact_digest(kind, key, body)}
    _event(db, event_id=key, event_type=kind, legacy_instance_id=scope["legacy_instance_id"],
           message="Synthetic planning capacity journal", payload=payload)
    return payload


def active_reservations(db, at):
    rows = db.scalars(select(LegacyOrchestrationEvent).where(LegacyOrchestrationEvent.event_type.in_((RESERVE, RELEASE))))
    holds = []
    released = set()
    for row in rows:
        payload = verified_record(row, row.event_type)
        if row.event_type == RELEASE:
            released.add(payload["reservation_id"])
        elif datetime.fromisoformat(payload["lease_expires_at"]) > at:
            holds.append(payload)
    return [hold for hold in holds if hold["reservation_id"] not in released]


def recent_scope_events(db, scope):
    """Retrieve durable planning outcomes without exposing neighboring scopes."""
    rows = db.scalars(select(LegacyOrchestrationEvent).where(
        LegacyOrchestrationEvent.event_type.in_((RESERVE, RELEASE)),
        LegacyOrchestrationEvent.legacy_instance_id == scope["legacy_instance_id"],
    ).order_by(LegacyOrchestrationEvent.id.desc()))
    result = []
    for row in rows:
        payload = verified_record(row, row.event_type)
        if payload["scope"] != scope:
            continue
        result.append({"event": row.event_type, "reservation_id": payload["reservation_id"],
                       "sha256": payload["sha256"], "external_authority": False})
        if len(result) == 8:
            break
    return result


def calendar(study, findings, reservations, at):
    status = {}
    for case in study.cases:
        if case.work_window is None:
            continue
        window = case.work_window
        blocking = [hold for hold in reservations if (
            window.occupied_from < datetime.fromisoformat(hold["occupied_until"])
            and datetime.fromisoformat(hold["occupied_from"]) < window.occupied_until
        )]
        status[case.kind] = {
            key: sorted(hold["sha256"] for hold in blocking if key in hold["candidate_ids"])
            for key in case.candidate_ids
            if any(key in hold["candidate_ids"] for hold in blocking)
        }
    # Date precision keeps reviewed artifacts stable across retries and UTC-day scoped.
    current = {candidate.candidate_id: bool(candidate.verified_capacity
               and candidate.verified_capacity.checked_at <= at < candidate.verified_capacity.expires_at)
               for candidate in study.candidates}
    return {"as_of": at.date().isoformat(), "conflicts": status, "evidence_current": current,
            "source_validity": {finding["source_id"]: finding["valid_through"] for finding in findings}}


def qualification(candidate, window, calendar, strategy):
    if calendar is None:
        return "CAPACITY_CALENDAR_UNCHECKED"
    evidence = candidate.verified_capacity
    if evidence is None or evidence.verification != "VERIFIED_IN_FIXTURE":
        return "CAPACITY_EVIDENCE_UNVERIFIED"
    as_of = datetime.fromisoformat(calendar["as_of"]).date()
    if (not calendar["evidence_current"].get(candidate.candidate_id)
            or not evidence.checked_at <= window.occupied_from < window.occupied_until <= evidence.expires_at
            or window.occupied_from.date() < as_of):
        return "CAPACITY_EVIDENCE_EXPIRED_OR_NOT_CURRENT"
    sources = [value for name, value in candidate.model_dump().items() if name.endswith("_source") and value]
    if not all(calendar["source_validity"].get(source, "") >= window.occupied_until.date().isoformat()
               for source in sources):
        return "CAPACITY_SOURCE_DOES_NOT_COVER_WINDOW"
    if not any(slot.starts_at <= window.occupied_from and window.occupied_until <= slot.ends_at
               for slot in evidence.availability):
        return "OUTSIDE_VERIFIED_WORKING_WINDOW"
    if any(window.occupied_from < slot.ends_at and slot.starts_at < window.occupied_until
           for slot in evidence.existing_assignments):
        return "EXISTING_ASSIGNMENT_OVERLAP"
    if candidate.candidate_id in calendar["conflicts"][strategy]:
        return "CAPACITY_ALREADY_RESERVED"
    return "CAPACITY_VERIFIED_IN_FIXTURE"
