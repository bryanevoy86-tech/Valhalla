"""Version-bound operating diligence for the existing Foundry evidence journal."""
from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import HTTPException
from pydantic import Field, model_validator
from sqlalchemy import inspect, select

from app.loki.evidence import artifact_digest
from app.models.completion_registry import LegacyOrchestrationEvent
from app.schemas.market_intelligence import MarketScope, StrictModel
from app.services.international_economics import InternationalStudy, project_international
from app.services.market_intelligence import authorized_source
from app.services.prime_business_execution import _json
from app.services.skilled_trade_economics import SkilledTradeStudy, project_trade


EVENT = "FOUNDRY_INDUSTRY_DILIGENCE"
EVENT_PREFIX = "FOUNDRY-INDUSTRY-"
INTERNATIONAL_PREFIX = "FOUNDRY-INTERNATIONAL-"
FACETS = (
    "CUSTOMER_NEEDS", "SALES", "COMPETITION", "COSTS", "REGULATION",
    "DISTRIBUTION", "AUTOMATION", "DEAL_TERMS", "FAILURE_MODES",
)
ROLE_FACETS = {
    "ODIN": ("COMPETITION", "DISTRIBUTION", "DEAL_TERMS"),
    "NJORD": ("COSTS", "DEAL_TERMS", "FAILURE_MODES"),
    "HUGINN": ("CUSTOMER_NEEDS", "COMPETITION", "DISTRIBUTION"),
    "FREYJA": ("CUSTOMER_NEEDS", "SALES", "DISTRIBUTION"),
    "BRAGI": ("CUSTOMER_NEEDS", "SALES"),
    "TYR": ("REGULATION", "DEAL_TERMS"),
    "FORSETI": ("REGULATION", "FAILURE_MODES"),
    "NORNS": ("COSTS", "FAILURE_MODES"),
    "MIMIR": ("AUTOMATION", "FAILURE_MODES"),
}
Facet = Literal["CUSTOMER_NEEDS", "SALES", "COMPETITION", "COSTS", "REGULATION",
                "DISTRIBUTION", "AUTOMATION", "DEAL_TERMS", "FAILURE_MODES"]
Minor = Annotated[int, Field(strict=True, ge=0, le=100_000_000)]


class Finding(StrictModel):
    facet: Facet
    source_id: str = Field(min_length=3, max_length=80)
    citation: str = Field(pattern=r"^https://[^/\s@]+/[^\s]*$", max_length=255)
    observed_on: date
    valid_through: date
    summary: str = Field(min_length=12, max_length=500)


class ExecutionOption(StrictModel):
    kind: Literal["BUILD", "BUY"]
    setup_minor: Minor
    monthly_minor: Minor
    setup_hours: Annotated[int, Field(strict=True, ge=0, le=10000)]
    monthly_hours: Annotated[int, Field(strict=True, ge=0, le=10000)]
    loaded_hour_minor: Minor
    dependencies: list[Annotated[str, Field(min_length=3, max_length=180)]] = Field(min_length=1, max_length=8)
    estimate_basis: str = Field(min_length=12, max_length=400)

    @model_validator(mode="after")
    def require_labor_basis(self):
        if (self.setup_hours or self.monthly_hours) and not self.loaded_hour_minor:
            raise ValueError("Include a loaded rate for the labor assumptions")
        return self


class IndustryDiligence(StrictModel):
    scope: MarketScope
    findings: list[Finding] = Field(min_length=1, max_length=18)
    execution_options: list[ExecutionOption] = Field(min_length=2, max_length=2)

    skilled_trade: SkilledTradeStudy | None = None
    international: InternationalStudy | None = None

    @model_validator(mode="after")
    def validate_comparison(self):
        if {item.kind for item in self.execution_options} != {"BUILD", "BUY"}:
            raise ValueError("Compare one build and one buy path")
        if len({(item.facet, item.source_id) for item in self.findings}) != len(self.findings):
            raise ValueError("Each source may support a facet once")
        if self.skilled_trade and not any(item.facet == "COSTS" for item in self.findings):
            raise ValueError("Skilled-trade assumptions require attributed cost evidence")
        if self.international:
            if self.skilled_trade:
                raise ValueError("Attach one operating model per industry study")
            model = self.international
            if not any(item.facet == "COSTS" and item.source_id == model.fx_source_id
                       and item.observed_on == model.fx_observed_on for item in self.findings):
                raise ValueError("FX needs a dated, attributed cost finding")
        return self


def event_id(evidence_id):
    return EVENT_PREFIX + str(evidence_id)


def check_sources(db, study, evidence, scope, today, *, lock=False):
    if study.scope.model_dump() != scope or evidence.evidence_class == "SIMULATION":
        raise HTTPException(409, "Industry diligence requires current scoped research")
    if study.skilled_trade and evidence.kind != "SERVICE":
        raise HTTPException(409, "Skilled-trade economics require scoped service evidence")
    if study.international:
        model = study.international
        if (model.kind != evidence.kind or evidence.currency != "CAD"
                or scope["jurisdiction"] != f"{model.country}-{model.region}"):
            raise HTTPException(409, "International scenario kind, CAD reporting or regional scope mismatch")
    for finding in sorted(study.findings, key=lambda item: item.source_id):
        source = authorized_source(db, finding.source_id, scope["jurisdiction"], "OPERATOR_REPORTED", lock=lock)
        if (source.source_type != "INDUSTRY_REFERENCE" or source.governance_status != "approved"
                or source.permission_status not in {"public", "licensed", "authorized"}
                or source.license_status not in {"government_open_data", "open", "licensed", "consented_internal_use"}
                or source.citation_ref != finding.citation
                or not finding.observed_on <= today <= finding.valid_through <= evidence.expires_on
                or (finding.valid_through - finding.observed_on).days > 90):
            raise HTTPException(409, "Industry source approval, citation or validity changed")


def build_record(db, row, evidence, scope, study, today):
    check_sources(db, study, evidence, scope, today, lock=True)
    content = study.model_dump(mode="json")
    if study.skilled_trade is None:
        content.pop("skilled_trade")
    else:
        content["skilled_trade"]["scenarios"].sort(key=lambda item: item["name"])
    if study.international is None:
        content.pop("international")
    else:
        content["international"]["professional_questions"].sort(key=lambda item: item["topic"])
    content["findings"].sort(key=lambda item: (item["facet"], item["source_id"]))
    content["execution_options"].sort(key=lambda item: item["kind"])
    body = {"evidence_sha256": row.digest, "industry": content}
    return {**body, "sha256": artifact_digest(EVENT, event_id(row.id), body)}


def project(body, evidence):
    content = body["industry"]
    findings = content["findings"]
    missing = [facet for facet in FACETS if not any(item["facet"] == facet for item in findings)]
    sources = sorted({item["source_id"] for item in findings})
    options = [{**option, "year_one_cost_minor": (
        option["setup_minor"] + 12 * option["monthly_minor"]
        + (option["setup_hours"] + 12 * option["monthly_hours"]) * option["loaded_hour_minor"]
    )} for option in content["execution_options"]]
    return {"sha256": body["sha256"], "currency": evidence.currency, "findings": findings,
            "source_ids": sources, "missing_facets": missing, "execution_options": options,
            "cost_basis": "DECLARED_ASSUMPTIONS_ONLY", "customer_demand_verified": False,
            "research_status": "MORE_RESEARCH_REQUIRED" if missing or len(sources) < 2 else "READY_FOR_CHALLENGE",
            "external_authority": False,
            **({"skilled_trade": project_trade(SkilledTradeStudy.model_validate(content["skilled_trade"]))}
               if "skilled_trade" in content else {}),
            **({"international": project_international(InternationalStudy.model_validate(content["international"]))}
               if "international" in content else {})}


def research_focus(role, industry):
    facets = ROLE_FACETS.get(role, FACETS)
    return {"review_facets": [facet for facet in facets if facet not in industry["missing_facets"]],
            "collect_missing_facets": [facet for facet in facets if facet in industry["missing_facets"]],
            "verify_buyer_outcomes": True}


def read_industry(db, row, evidence, scope, today, *, lock=False):
    if not inspect(db.connection()).has_table(LegacyOrchestrationEvent.__tablename__):
        return None
    query = select(LegacyOrchestrationEvent).filter_by(event_id=event_id(row.id))
    receipt = db.scalar(query.with_for_update().execution_options(populate_existing=True) if lock else query)
    if receipt is None:
        return None
    body = _json(receipt.payload_json, {})
    try:
        assert_body = {"evidence_sha256": row.digest, "industry": body["industry"]}
        if (receipt.event_type != EVENT or receipt.legacy_instance_id != scope["legacy_instance_id"]
                or body.get("evidence_sha256") != row.digest
                or body.get("sha256") != artifact_digest(EVENT, receipt.event_id, assert_body)):
            raise ValueError
        study = IndustryDiligence.model_validate(body["industry"])
    except (TypeError, ValueError, AttributeError, KeyError):
        raise HTTPException(409, "Industry diligence failed integrity verification") from None
    check_sources(db, study, evidence, scope, today, lock=lock)
    return project(body, evidence)


def read_industry_reassessment(db, trigger_id, scope, today, *, international=False):
    from app.models.foundry_evidence import FoundryEvidence
    from app.services.foundry_discovery import checked_evidence

    prefix, field = (INTERNATIONAL_PREFIX, "international") if international else (EVENT_PREFIX, "skilled_trade")
    try:
        evidence_id = UUID(trigger_id.removeprefix(prefix))
    except ValueError:
        raise HTTPException(409, "Invalid industry reassessment reference") from None
    row = db.get(FoundryEvidence, evidence_id, populate_existing=True)
    if row is None or prefix + str(row.id) != trigger_id:
        raise HTTPException(409, "Industry reassessment evidence unavailable")
    evidence = checked_evidence(row, scope, today, db=db)
    industry = read_industry(db, row, evidence, scope, today)
    projection = (industry or {}).get(field)
    if not projection:
        raise HTTPException(409, "Industry reassessment projection unavailable")
    return {"evidence_id": str(row.id), "evidence_sha256": row.digest,
            "industry_sha256": industry["sha256"], field: projection}
