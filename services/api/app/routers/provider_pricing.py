"""Reconcile recorded specialist token counts against dated price evidence."""
from datetime import date, datetime, timedelta, timezone
from typing import Literal
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.dependencies import require_prime_control_key
from app.loki.evidence import artifact_digest
from app.models.model_provider import ModelProvider
from app.models.owner_conversation import OwnerInferenceAttempt
from app.models.provider_pricing import ProviderPriceQuote, ProviderUsageReconciliation
from app.models.specialist_probe import SpecialistProbe
from app.routers.provider_evidence import identity, recommend
from app.pantheon.roles import Role
from app.services.prime_business_execution import require_owner_mandate_key


def schema(db: Session = Depends(get_db)):
    inspector = inspect(db.connection())
    if any(not inspector.has_table(model.__tablename__) for model in (ProviderPriceQuote, ProviderUsageReconciliation)):
        raise HTTPException(503, "Provider pricing evidence schema unavailable")


router = APIRouter(prefix="/api/prime/provider-intelligence", tags=["provider-pricing"],
                   dependencies=[Depends(require_prime_control_key), Depends(schema)])
owner = [Depends(require_owner_mandate_key)]
hosts = {"groq": {"groq.com", "console.groq.com"}, "openai": {"openai.com", "platform.openai.com"}}


class QuoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    quote_id: UUID
    provider_id: int = Field(gt=0)
    source_url: str = Field(min_length=8, max_length=300)
    observed_on: date
    effective_on: date
    expires_on: date
    currency: Literal["USD", "CAD"]
    input_minor_per_million: int = Field(strict=True, ge=0, le=100_000_000)
    output_minor_per_million: int = Field(strict=True, ge=0, le=100_000_000)


class ReconcileIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    quote_id: UUID
    statement_ref: str = Field(min_length=5, max_length=240)
    reported_microminor: int = Field(strict=True, ge=0, le=100_000_000_000_000)


def _quote_digest(quote):
    return artifact_digest("provider_price_quote", str(quote.id), {
        "provider_id": quote.provider_id, "vendor": quote.vendor, "model": quote.model, "source_url": quote.source_url,
        "observed_on": quote.observed_on.isoformat(), "effective_on": quote.effective_on.isoformat(),
        "expires_on": quote.expires_on.isoformat(), "currency": quote.currency,
        "input_minor_per_million": quote.input_minor_per_million,
        "output_minor_per_million": quote.output_minor_per_million,
    })


def _quote(quote):
    if quote.sha256 != _quote_digest(quote):
        raise HTTPException(409, "Provider price evidence changed")
    return {
        "quote_id": quote.id, "provider_id": quote.provider_id, "vendor": quote.vendor, "model": quote.model,
        "source_url": quote.source_url, "currency": quote.currency, "sha256": quote.sha256,
        "input_minor_per_million": quote.input_minor_per_million, "output_minor_per_million": quote.output_minor_per_million,
        "observed_on": quote.observed_on, "effective_on": quote.effective_on, "expires_on": quote.expires_on,
        "basis": "OWNER_RECORDED_PRICE_SOURCE",
    }


@router.post("/price-quotes", status_code=201, dependencies=owner)
def record_quote(payload: QuoteIn, db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).date()
    if (payload.observed_on > today or not payload.effective_on <= payload.expires_on
            or payload.expires_on - payload.effective_on > timedelta(days=366)):
        raise HTTPException(422, "Quote validity dates are invalid")
    provider = db.get(ModelProvider, payload.provider_id)
    registered = identity(provider) if provider and provider.active else None
    if registered is None:
        raise HTTPException(409, "An active registered model is required")
    vendor, model = registered
    try:
        url = urlsplit(payload.source_url)
        if (url.scheme != "https" or url.hostname not in hosts[vendor] or not url.path
                or url.username or url.password or url.port not in {None, 443} or url.query or url.fragment):
            raise ValueError
    except ValueError:
        raise HTTPException(422, "Use a credential-free provider documentation URL") from None
    quote = ProviderPriceQuote(id=payload.quote_id, vendor=vendor, model=model,
                               **payload.model_dump(exclude={"quote_id"}), sha256="")
    quote.sha256 = _quote_digest(quote)
    prior = db.get(ProviderPriceQuote, quote.id)
    if prior:
        if prior.sha256 != quote.sha256:
            raise HTTPException(409, "Price quote ID already used")
        return _quote(prior)
    db.add(quote)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Price quote ID or effective date already used") from None
    return _quote(quote)


@router.get("/price-quotes")
def list_quotes(provider_id: int, db: Session = Depends(get_db)):
    rows = db.scalars(select(ProviderPriceQuote).filter_by(provider_id=provider_id)
                      .order_by(ProviderPriceQuote.effective_on.desc()).limit(50)).all()
    return [_quote(row) for row in rows]


def _comparison(db, probe_id, quote_id):
    # Both records are the existing synthetic transport receipts.
    probe = db.get(SpecialistProbe, probe_id)
    attempt = db.get(OwnerInferenceAttempt, probe_id)
    quote = db.get(ProviderPriceQuote, quote_id)
    if not probe or not attempt or not quote:
        raise HTTPException(404, "Probe usage or price evidence unavailable")
    _quote(quote)
    used_on = date.fromisoformat(attempt.day)
    if (probe.provider_id, attempt.vendor, attempt.model) != (quote.provider_id, quote.vendor, quote.model) or probe.model != quote.model:
        raise HTTPException(409, "Price quote does not match the metered model")
    if not quote.effective_on <= used_on <= quote.expires_on:
        raise HTTPException(409, "Price quote does not cover the usage date")
    if any(type(count) is not int or count < 0 for count in (attempt.prompt_tokens, attempt.completion_tokens)):
        raise HTTPException(409, "Provider usage counts are incomplete")
    estimated = attempt.prompt_tokens * quote.input_minor_per_million + attempt.completion_tokens * quote.output_minor_per_million
    evidence = artifact_digest("provider_probe_usage", str(probe_id), {
        "quote_sha256": quote.sha256, "usage_day": attempt.day,
        "prompt_tokens": attempt.prompt_tokens, "completion_tokens": attempt.completion_tokens,
    })
    return {"probe_id": str(probe_id), "quote_id": str(quote_id), "currency": quote.currency,
            "estimated_microminor": estimated, "usage_sha256": evidence, "billing_provider_verified": False}


@router.get("/stage-probes/{probe_id}/cost")
def estimate_cost(probe_id: UUID, quote_id: UUID, db: Session = Depends(get_db)):
    return _comparison(db, probe_id, quote_id)


@router.post("/stage-probes/{probe_id}/reconcile", status_code=201, dependencies=owner)
def reconcile(probe_id: UUID, payload: ReconcileIn, db: Session = Depends(get_db)):
    result = _comparison(db, probe_id, payload.quote_id)
    row = db.get(ProviderUsageReconciliation, probe_id)
    entries = (payload.quote_id, payload.statement_ref, payload.reported_microminor, result["usage_sha256"])
    if row:
        if (row.quote_id, row.statement_ref, row.reported_microminor, row.usage_sha256) != entries:
            raise HTTPException(409, "Probe already has different reconciliation evidence")
    else:
        db.add(ProviderUsageReconciliation(
            probe_id=probe_id, quote_id=payload.quote_id, statement_ref=payload.statement_ref,
            estimated_microminor=result["estimated_microminor"], reported_microminor=payload.reported_microminor,
            usage_sha256=result["usage_sha256"],
        ))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, "Probe reconciliation already recorded") from None
    return {**result, "statement_ref": payload.statement_ref, "reported_microminor": payload.reported_microminor,
            "variance_microminor": payload.reported_microminor - result["estimated_microminor"],
            "basis": "OWNER_REPORTED_STATEMENT"}


class RouteBudget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role
    data_class: Literal["SYNTHETIC"]
    currency: Literal["USD", "CAD"]
    input_token_limit: int = Field(strict=True, ge=1, le=8000)
    output_token_limit: int = Field(strict=True, ge=1, le=2000)
    max_microminor: int = Field(strict=True, ge=0, le=100_000_000_000_000)


@router.post("/select-staging-candidate", dependencies=owner)
def select_staging_candidate(payload: RouteBudget, db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).date()
    matches = []
    for candidate in recommend(payload.role, payload.data_class, db)["candidates"]:
        quote = db.scalar(select(ProviderPriceQuote).filter_by(
            provider_id=candidate["provider_id"], model=candidate["model"], vendor=candidate["vendor"],
            currency=payload.currency,
        ).where(ProviderPriceQuote.effective_on <= today, ProviderPriceQuote.expires_on >= today)
            .order_by(ProviderPriceQuote.effective_on.desc()).limit(1))
        if quote is None:
            continue
        _quote(quote)
        maximum = (payload.input_token_limit * quote.input_minor_per_million
                   + payload.output_token_limit * quote.output_minor_per_million)
        if maximum <= payload.max_microminor:
            matches.append({
                "provider_id": quote.provider_id, "vendor": quote.vendor, "model": quote.model,
                "quote_id": str(quote.id), "quote_sha256": quote.sha256,
                "benchmark_evidence_id": str(candidate["evidence_id"]), "estimated_max_microminor": maximum,
            })
    selected = min(matches, key=lambda item: (item["estimated_max_microminor"], item["provider_id"])) if matches else None
    return {"role": payload.role, "candidate": selected, "currency": payload.currency,
            "mode": "ADVISORY_SYNTHETIC_SELECTION", "provider_call_authorized": False}
