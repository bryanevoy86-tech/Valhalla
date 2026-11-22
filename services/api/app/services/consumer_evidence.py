"""Consent-aware aggregate behavioural research bound to existing Foundry evidence."""
from datetime import date, timedelta
from math import ceil, floor, sqrt
from typing import Annotated, Literal

from fastapi import HTTPException
from pydantic import Field, model_validator
from sqlalchemy import inspect, select

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.prime_business_execution import _json

EVENT = "FOUNDRY_CONSUMER_EVIDENCE"
Count = Annotated[int, Field(strict=True, ge=0, le=100_000)]
Signal = Literal[
    "SAVE_TIME", "REDUCE_COST", "QUALITY", "CONVENIENCE", "UNDERSERVED_NEED", "EMERGING_DEMAND",
    "PRICE_OBJECTION", "UNCLEAR_VALUE", "CHECKOUT_FRICTION", "TRUST_CONCERN", "SATISFACTION",
    "REPEAT_INTENT", "VOLUNTARY_REFERRAL", "REGIONAL_FIT",
]


class Observation(StrictModel):
    signal: Signal
    count: Count


class PriceArm(StrictModel):
    cad_price_minor: int = Field(strict=True, gt=0, le=100_000_000)
    exposed: Count
    chose_offer: Count


class ConsumerEvidence(StrictModel):
    scope: MarketScope
    observation_end: date
    source_basis: Literal["SYNTHETIC", "PERMISSIBLE_PUBLIC_AGGREGATE", "CONSENTED_FIRST_PARTY_AGGREGATE"]
    aggregate_sample: int = Field(strict=True, ge=20, le=100_000)
    observations: list[Observation] = Field(min_length=1, max_length=14)
    offer_experiment: list[PriceArm] = Field(default_factory=list, max_length=2)
    transparent_offer_and_terms: Literal[True]
    voluntary_participation: Literal[True]
    no_deceptive_claims_or_urgency: Literal[True]
    no_sensitive_profiling_or_vulnerability_targeting: Literal[True]
    no_fake_endorsements_or_manipulative_interfaces: Literal[True]

    @model_validator(mode="after")
    def cohort_integrity(self):
        if (len({item.signal for item in self.observations}) != len(self.observations)
                or any(item.count > self.aggregate_sample or 0 < item.count < 5
                       or 0 < self.aggregate_sample - item.count < 5 for item in self.observations)):
            raise ValueError("Report distinct aggregate signals and suppress small cells")
        arms = self.offer_experiment
        if arms and (len(arms) != 2 or arms[0].cad_price_minor >= arms[1].cad_price_minor
                     or sum(arm.exposed for arm in arms) > self.aggregate_sample
                     or any(arm.exposed < 20 or arm.chose_offer > arm.exposed or 0 < arm.chose_offer < 5
                            or 0 < arm.exposed - arm.chose_offer < 5 for arm in arms)):
            raise ValueError("Use two distinct increasing price arms and suppress small cells")
        return self


def event_id(demand_id):
    return f"FOUNDRY-BEHAVIOR-{demand_id}"


def interval(successes, sample):
    # Wilson 95% interval for descriptive binomial rates, rounded outward.
    rate = successes / sample
    z = 1.96
    denom = 1 + z * z / sample
    center = (rate + z * z / (2 * sample)) / denom
    half = z * sqrt(rate * (1 - rate) / sample + z * z / (4 * sample * sample)) / denom
    return {"rate_bp": successes * 10000 // sample,
            "interval_low_bp": max(0, floor((center - half) * 10000)),
            "interval_high_bp": min(10000, ceil((center + half) * 10000))}


def project(body):
    study = ConsumerEvidence.model_validate(body["research"])
    arms = [{**arm.model_dump(), **interval(arm.chose_offer, arm.exposed)} for arm in study.offer_experiment]
    signals = [{**item.model_dump(), **interval(item.count, study.aggregate_sample)} for item in study.observations]
    overlapping = len(arms) != 2 or (arms[0]["interval_low_bp"] <= arms[1]["interval_high_bp"]
                                     and arms[1]["interval_low_bp"] <= arms[0]["interval_high_bp"])
    observed = {item.signal for item in study.observations if item.count}
    actions = [
        action for action, categories in (
            ("VALIDATE_PRODUCT_VALUE", {"SAVE_TIME", "REDUCE_COST", "QUALITY", "CONVENIENCE", "UNDERSERVED_NEED"}),
            ("TEST_TRANSPARENT_PRICING", {"PRICE_OBJECTION", "UNCLEAR_VALUE"}),
            ("SIMPLIFY_CHECKOUT", {"CHECKOUT_FRICTION"}),
            ("VERIFY_TRUST_AND_SUPPORT", {"TRUST_CONCERN", "SATISFACTION"}),
            ("VALIDATE_LOCAL_MARKET_FIT", {"REGIONAL_FIT", "EMERGING_DEMAND"}),
            ("MEASURE_RETURN_AND_VOLUNTARY_REFERRALS", {"REPEAT_INTENT", "VOLUNTARY_REFERRAL"}),
        ) if observed & categories
    ]
    return {"demand_evidence_id": body["demand_evidence_id"], "sha256": body["sha256"],
            "scope": study.scope.model_dump(), "buyer_segment": body["buyer_segment"],
            "source_basis": study.source_basis, "independent_study_source_verified": False,
            "observed_through": study.observation_end.isoformat(), "sample": study.aggregate_sample,
            "signals": signals, "offer_arms": arms,
            "research_actions": actions,
            "price_signal": ("NO_OFFER_EXPERIMENT" if not arms else
                             "NO_CLEAR_SEPARATION" if overlapping else "DESCRIPTIVE_DIFFERENCE"),
            "confidence": "AGGREGATE_DESCRIPTIVE_ONLY", "causality_verified": False,
            "settled_conversion_verified": False, "independent_review_required": True,
            "external_action_authorized": False}


def build_record(row, evidence, scope, study, today):
    if (not evidence.provenance or evidence.currency != "CAD" or study.scope.model_dump() != scope
            or not max(evidence.observed_on, today - timedelta(days=90)) <= study.observation_end
            <= min(today, evidence.expires_on)):
        raise HTTPException(409, "Current scoped sourced CAD demand and an aligned study are required")
    body = {"demand_evidence_id": str(row.id), "demand_sha256": row.digest,
            "buyer_segment": evidence.provenance.buyer_segment, "research": study.model_dump(mode="json")}
    return {**body, "sha256": artifact_digest("foundry_consumer_evidence", event_id(row.id), body)}


def reviewed_summary(research):
    return {key: research[key] for key in (
        "sha256", "confidence", "price_signal", "research_actions", "settled_conversion_verified",
    )}


def read_consumer_evidence(db, row, evidence, scope, today):
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        return None
    receipt = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=event_id(row.id)))
    if receipt is None:
        return None
    body = _json(receipt.payload_json, {})
    try:
        study = ConsumerEvidence.model_validate(body["research"])
        if (receipt.event_type != EVENT or receipt.legacy_instance_id != scope["legacy_instance_id"]
                or study.observation_end < today - timedelta(days=90)
                or body != build_record(row, evidence, scope, study, today)):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise HTTPException(409, "Consumer research is stale, out of scope or changed") from None
    return project(body)
