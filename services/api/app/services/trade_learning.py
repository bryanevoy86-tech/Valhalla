"""Version-bound synthetic construction learning in the existing Foundry journal."""
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field
from sqlalchemy import select

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.prime_business_execution import _json
from app.services.skilled_trade_economics import Days, Money, Workers

FORECAST_PREFIX = "TRADE-FORECAST-"
LESSON_PREFIX = "TRADE-LESSON-"
FORECAST_EVENT = "FOUNDRY_TRADE_FORECAST"
LESSON_EVENT = "FOUNDRY_TRADE_LESSON"
BASIS = "CONSTRUCTION_OUTCOME_FIXTURE_ONLY"


class ForecastRequest(StrictModel):
    scope: MarketScope
    opportunity_key: str = Field(min_length=3, max_length=100)
    independent_review_id: UUID
    horizon_days: Annotated[int, Field(strict=True, ge=1, le=90)]


class OutcomeRequest(StrictModel):
    scope: MarketScope
    forecast_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_ref: str = Field(pattern=r"^fixture:[A-Za-z0-9._/-]+$", max_length=160)
    completed_jobs: Annotated[int, Field(strict=True, ge=0, le=100)]
    on_site_days_per_job: Days
    available_skilled_workers: Workers
    earned_revenue_minor: Money
    operating_cost_excluding_callbacks_minor: Money
    callback_cost_minor: Money
    payment_days_after_delivery: Days
    uncommitted_cash_minor: Money


def sealed(kind, event_id, content):
    return {**content, "sha256": artifact_digest(kind, event_id, content)}


def read_record(db, kind, ref):
    row = db.scalar(select(LegacyOrchestrationEvent).filter_by(event_id=ref).execution_options(populate_existing=True))
    if row is None:
        return None
    record = _json(row.payload_json, {})
    if isinstance(record, dict):
        fields = {key: value for key, value in record.items() if key != "sha256"}
        if (row.event_type == kind and isinstance(record.get("scope"), dict)
                and row.legacy_instance_id == record["scope"].get("legacy_instance_id")
                and record == sealed(kind, ref, fields)):
            return record
    raise HTTPException(409, "Trade learning receipt failed integrity checks")


def project_lesson(forecast, outcome, observed_at):
    from app.pantheon.forecasts import operating_contribution_error

    contribution = (outcome["earned_revenue_minor"] - outcome["operating_cost_excluding_callbacks_minor"]
                    - outcome["callback_cost_minor"])
    variance = operating_contribution_error(forecast["prediction"], contribution, observed_at)
    deviations = {
        "completed_jobs": outcome["completed_jobs"] - forecast["baseline"]["completed_jobs"],
        "on_site_days_per_job": outcome["on_site_days_per_job"] - forecast["baseline"]["on_site_days_per_job"],
        "available_skilled_workers": outcome["available_skilled_workers"] - forecast["baseline"]["available_skilled_workers"],
        "callback_cost_minor": outcome["callback_cost_minor"] - forecast["baseline"]["callback_cost_minor"],
        "payment_days_after_delivery": outcome["payment_days_after_delivery"] - forecast["baseline"]["payment_days_after_delivery"],
    }
    cash_shortfall = max(0, forecast["baseline"]["required_cash_minor"] - outcome["uncommitted_cash_minor"])
    blockers = [name for active, name in (
        (contribution < 0, "TRADE_FIXTURE_OPERATING_LOSS"),
        (deviations["completed_jobs"] < 0 or deviations["on_site_days_per_job"] > 0, "TRADE_PRODUCTION_MISSED"),
        (deviations["available_skilled_workers"] < 0, "TRADE_SKILLED_CAPACITY_LOST"),
        (deviations["callback_cost_minor"] > 0, "TRADE_CALLBACK_OVERRUN"),
        (deviations["payment_days_after_delivery"] > 0, "TRADE_RECEIVABLE_DELAY"),
        (cash_shortfall > 0, "TRADE_WORKING_CAPITAL_SHORTFALL"),
    ) if active]
    return {
        "basis": BASIS, "scope": forecast["scope"], "evidence_id": forecast["evidence_id"],
        "evidence_sha256": forecast["evidence_sha256"], "industry_sha256": forecast["industry_sha256"],
        "opportunity_record_id": forecast["opportunity_record_id"], "forecast_sha256": forecast["sha256"],
        "observed_at": observed_at, "outcome": outcome, "variance": variance,
        "operating_deviations": deviations, "cash_shortfall_minor": cash_shortfall, "blockers": blockers,
        "evidence_count": 1, "calibration": "INSUFFICIENT_SAMPLE_FOR_GENERALIZATION",
        "external_authority": False, "verified_commercial_revenue": False,
    }


def current_lesson(db, row, scope, industry, opportunity_record_id, today):
    from app.routers.foundry_operating_rehearsal import enabled

    if not enabled():
        return None
    reference = LESSON_PREFIX + str(row.id)
    lesson = read_record(db, LESSON_EVENT, reference)
    if lesson is None:
        return None
    forecast = read_record(db, FORECAST_EVENT, FORECAST_PREFIX + str(row.id))
    try:
        if (forecast is None or forecast["scope"] != scope or forecast["evidence_id"] != str(row.id)
                or forecast["evidence_sha256"] != row.digest or forecast["industry_sha256"] != industry["sha256"]):
            raise ValueError
        observed = datetime.fromisoformat(lesson["observed_at"])
        issued = datetime.fromisoformat(forecast["issued_at"])
        if not issued <= observed <= datetime.fromisoformat(forecast["prediction"]["deadline_at"]) or observed.date() > today:
            raise ValueError
        outcome = OutcomeRequest.model_validate(lesson["outcome"]).model_dump(mode="json")
        if outcome["scope"] != scope or outcome["forecast_sha256"] != forecast["sha256"]:
            raise ValueError
        expected = sealed(LESSON_EVENT, reference, project_lesson(forecast, outcome, lesson["observed_at"]))
        if lesson != expected:
            raise ValueError
    except (KeyError, ValueError, TypeError):
        raise HTTPException(409, "Trade lesson lacks intact scoped evidence") from None
    if forecast["opportunity_record_id"] != str(opportunity_record_id):
        return None
    return {"forecast": forecast, "lesson": lesson}


def lesson_for_trigger(assessment, event):
    for item in assessment.get("trade_learning", []):
        if event == LESSON_PREFIX + item["lesson"]["evidence_id"]:
            return item
    raise HTTPException(409, "Trade outcome trigger lacks current scoped evidence")
