"""Private startup planning over dated public fees and owner-supplied CAD estimates."""
from datetime import date, datetime, timedelta, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Money = Annotated[int, Field(strict=True, ge=0, le=100_000_000_000)]
Label = Annotated[str, Field(min_length=1, max_length=120)]
Route = Literal["MANITOBA", "FEDERAL_CANADA", "INTERNATIONAL_FIRST"]
MANITOBA = "https://companiesoffice.gov.mb.ca/starting_manitoba_corporation.html"
MANITOBA_FORMS = "https://companiesoffice.gov.mb.ca/forms_mbcorporations.html"
FEDERAL = "https://ised-isde.canada.ca/site/corporations-canada/en/services-fees-and-processing-times"
EXTRA_PROVINCIAL = "https://companiesoffice.gov.mb.ca/starting_extra_provincial.html"
EXTRA_PROVINCIAL_FORMS = "https://companiesoffice.gov.mb.ca/forms_extraprovincialcorporations.html"
PANAMA = "https://www.panamadigital.gob.pa/InformacionTramite/constitucion-de-sociedades-y-fundaciones-de-interes-privado"
CORPORATE_RESIDENCY = "https://www.canada.ca/en/revenue-agency/services/tax/international-non-residents/businesses-international-non-resident-taxes/residency-a-corporation.html"
DEPARTURE = "https://www.canada.ca/en/revenue-agency/services/tax/international-non-residents/individuals-leaving-entering-canada-non-residents/leaving-canada-emigrants.html"
FEE_CHECKED_ON = date(2026, 11, 21)
REQUIRED_QUOTES = ("corporate_legal", "tax_and_accounting")
OBJECTIVES = {
    "holding_company": "Compare a single operating entity with a later HoldCo and document shareholder control before filing.",
    "intellectual_property": "Record ownership and licensing of existing IP and obtain a valuation and tax review before any assignment.",
    "trust": "Ask counsel to compare direct versus trust ownership, control, beneficial ownership and reporting before settling a trust.",
    "subsidiaries_and_regional_mirrors": "Identify legal registration and permits by market. An internal mirror is an operational scope.",
    "canada_exit": "Ask cross-border advisers to model personal versus corporate residency, deemed dispositions, continuity and any reorganization.",
    "residency_and_tax": "Review actual central management and control, applicable statutes and treaties, permanent establishments and tax accounts.",
    "reporting": "Obtain a calendar for corporate filings, tax, beneficial ownership and any applicable foreign reporting.",
}


class PrivateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Infrastructure(PrivateInput):
    key: Label
    label: Label
    funded_to_date_minor: Money
    committed_monthly_minor: Money = 0


class Cost(PrivateInput):
    key: Label
    label: Label
    cadence: Literal["ACTIVATION", "MONTHLY", "ANNUAL"]
    basis: Literal["PROFESSIONAL_QUOTE", "OWNER_ESTIMATE", "UNAVAILABLE"]
    amount_minor: Money | None = None
    route: Route | None = None
    reference: Label | None = None

    @model_validator(mode="after")
    def match_evidence(self):
        if (self.amount_minor is None) != (self.basis == "UNAVAILABLE"):
            raise ValueError("Cost amount must match availability")
        if self.basis == "PROFESSIONAL_QUOTE" and self.reference is None:
            raise ValueError("Professional quotes require a private reference")
        return self


class SurplusAsset(PrivateInput):
    label: Label
    owner_valuation_minor: Money


class ProfessionalReviewFact(PrivateInput):
    label: Label
    statement: str = Field(min_length=1, max_length=400)
    source_reference: Label
    observed_on: date


class ProfessionalReviewIntake(PrivateInput):
    route: Route
    topic: Literal["CORPORATE_STRUCTURE", "TAX_RESIDENCY", "IP_OWNERSHIP", "TRUST_AND_SUCCESSION", "REGISTRATION"]
    facts: list[ProfessionalReviewFact] = Field(min_length=1, max_length=12)
    questions: list[str] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_questions(self):
        self.questions = [question.strip() for question in self.questions]
        if any(not question or len(question) > 400 for question in self.questions):
            raise ValueError("Questions must be between one and 400 characters")
        return self


class StartupPlanIn(PrivateInput):
    manitoba_operations: bool
    named_corporation: bool
    international_jurisdiction: Label = "Panama"
    funded_infrastructure: list[Infrastructure] = Field(default_factory=list, max_length=50)
    costs: list[Cost] = Field(default_factory=list, max_length=80)
    startup_cash_available_minor: Money | None = None
    operating_reserve_target_minor: Money | None = None
    operating_cash_available_minor: Money | None = None
    surplus_assets: list[SurplusAsset] = Field(default_factory=list, max_length=50)
    professional_review: list[ProfessionalReviewIntake] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def avoid_double_counting(self):
        keys = {(cost.route, cost.key.casefold()) for cost in self.costs}
        funded = {item.key.casefold() for item in self.funded_infrastructure}
        common = {key for route, key in keys if route is None}
        required = {*REQUIRED_QUOTES, "foreign_filing_cad"}
        if (len(keys) != len(self.costs) or len(funded) != len(self.funded_infrastructure)
                or any(key in funded or key.startswith("registry:") for _, key in keys)
                or any(route is not None and key in common for route, key in keys)
                or any(cost.key.casefold() in required and cost.cadence != "ACTIVATION" for cost in self.costs)):
            raise ValueError("Cost keys must identify distinct incremental obligations")
        return self


def registry_fee(key, label, amount, source, today, cadence="ACTIVATION"):
    current = FEE_CHECKED_ON <= today <= FEE_CHECKED_ON + timedelta(days=90)
    return {
        "key": f"registry:{key}", "label": label, "cadence": cadence,
        "basis": "VERIFIED_GOVERNMENT_FEE" if current else "NEEDS_GOVERNMENT_RECHECK",
        "amount_minor": amount if current else None, "reference": source,
        "source_checked_on": FEE_CHECKED_ON.isoformat(),
    }


def government_items(route, request, today):
    def fee(key, label, amount, source, cadence="ACTIVATION"):
        return registry_fee(key, label, amount, source, today, cadence)

    rows = []
    if route == "MANITOBA":
        rows.extend([
            fee("mb_articles", "Manitoba articles of incorporation", 35000, MANITOBA),
            fee("mb_return", "Manitoba share corporation annual return", 6500, MANITOBA_FORMS, "ANNUAL"),
        ])
    if route == "FEDERAL_CANADA":
        rows += [
            fee("ca_articles", "Federal online incorporation", 20000, FEDERAL),
            fee("ca_return", "Federal annual return", 1200, FEDERAL, "ANNUAL"),
        ]
    manitoba_registration = route != "MANITOBA" and request.manitoba_operations
    if manitoba_registration:
        rows.extend([
            fee("mb_registration", "Manitoba extra-provincial registration", 35000, EXTRA_PROVINCIAL),
            fee("mb_extra_return", "Manitoba extra-provincial share corporation annual return", 6500,
                EXTRA_PROVINCIAL_FORMS, "ANNUAL"),
        ])
    if request.named_corporation and (manitoba_registration or route == "MANITOBA"):
        rows.append(fee("mb_name", "Manitoba name reservation", 4500, MANITOBA if route == "MANITOBA" else EXTRA_PROVINCIAL))
    return rows


def compare_route(route, request, today):
    rows = [entry.model_dump(exclude={"route"}) for entry in request.costs if entry.route in (None, route)]
    required = dict(corporate_legal="Corporate structure and filing review", tax_and_accounting="Tax and accounting setup")
    if route == "INTERNATIONAL_FIRST":
        required["foreign_filing_cad"] = "Foreign registration and local setup, quoted or converted to CAD"
    provided = {row["key"].casefold() for row in rows}
    for key, label in required.items():
        if key not in provided:
            rows.append({"key": key, "label": label, "cadence": "ACTIVATION", "basis": "UNAVAILABLE", "amount_minor": None})
    rows = government_items(route, request, today) + rows
    activation = [row for row in rows if row["cadence"] == "ACTIVATION"]
    verified = sum(row["amount_minor"] for row in activation if row["basis"] == "VERIFIED_GOVERNMENT_FEE")
    quoted = sum(row["amount_minor"] for row in activation if row["basis"] == "PROFESSIONAL_QUOTE")
    estimate = sum(row["amount_minor"] for row in activation if row["basis"] == "OWNER_ESTIMATE")
    unknown = [row["key"] for row in activation if row["amount_minor"] is None]
    fully_quoted = not unknown and all(row["basis"] != "OWNER_ESTIMATE" for row in activation)
    known_floor = verified + quoted
    cash = request.startup_cash_available_minor
    recurring = [row for row in rows if row["cadence"] != "ACTIVATION"]
    existing_monthly = sum(item.committed_monthly_minor for item in request.funded_infrastructure)
    annual_known = 12 * existing_monthly + sum((row["amount_minor"] or 0) * (12 if row["cadence"] == "MONTHLY" else 1)
                                               for row in recurring)
    operating_cash = request.operating_cash_available_minor
    unknown_recurring = [row["key"] for row in recurring if row["amount_minor"] is None]
    reserve = request.operating_reserve_target_minor
    return {
        "route": route, "jurisdiction": {"MANITOBA": "Manitoba", "FEDERAL_CANADA": "Canada (federal)",
                                        "INTERNATIONAL_FIRST": request.international_jurisdiction}[route],
        "objectives": OBJECTIVES,
        "route_review": {
            "MANITOBA": "Review local filing, extra-provincial registration triggers and future HoldCo/IP restructuring.",
            "FEDERAL_CANADA": "Review federal filings, Manitoba registration and any local service appointment, and records across jurisdictions.",
            "INTERNATIONAL_FIRST": "Review local entity, agent and banking eligibility, Canadian management/residency, foreign reporting and dual-jurisdiction costs.",
        }[route],
        "additional_sources": ([PANAMA] if route == "INTERNATIONAL_FIRST" and
                               request.international_jurisdiction.casefold() == "panama" else []),
        "activation": {
            "items": activation, "verified_government_minor": verified, "professional_quote_minor": quoted,
            "owner_estimate_minor": estimate, "unpriced_keys": unknown, "known_and_estimated_minor": known_floor + estimate,
            "estimate_including_all_items_minor": None if unknown else known_floor + estimate,
            "additional_capital_floor_minor": max(0, known_floor - cash) if cash is not None else None,
            "estimated_additional_capital_minor": max(0, known_floor + estimate - cash)
            if cash is not None and not unknown else None,
            "minimum_additional_capital_minor": max(0, known_floor - cash) if cash is not None and fully_quoted else None,
        },
        "operating": {
            "incremental_recurring_items": recurring, "existing_committed_monthly_minor": existing_monthly,
            "known_annual_cost_minor": annual_known, "reserve_target_minor": reserve,
            "unpriced_recurring_keys": unknown_recurring,
            "available_operating_cash_minor": operating_cash,
            "known_cost_runway_months": (round(operating_cash * 12 / annual_known, 2)
                                         if operating_cash is not None and annual_known and not unknown_recurring else None),
            "reserve_gap_minor": max(0, reserve - operating_cash)
            if reserve is not None and operating_cash is not None else None,
            "estimate_only": True,
        },
    }


CHECKLIST = (
    ("Inventory funded services and confirm liquid startup cash", ("OWNER",)),
    ("Review corporate structure, IP, trust fit, cross-border tax and reporting", ("QUALIFIED_PROFESSIONAL", "OWNER")),
    ("Approve jurisdiction, quotes and filing instructions", ("OWNER", "QUALIFIED_PROFESSIONAL")),
    ("Register corporation, permits and applicable tax accounts", ("OWNER", "QUALIFIED_PROFESSIONAL", "EXTERNAL_AUTHORIZATION")),
    ("Open and reconcile business banking and accounting", ("OWNER", "QUALIFIED_PROFESSIONAL", "EXTERNAL_AUTHORIZATION")),
    ("Commission approved technical services and run staging acceptance", ("OWNER", "EXTERNAL_AUTHORIZATION")),
    ("Verify acceptance, legal, financial and authorization gates before controlled commercial startup", ("OWNER", "EXTERNAL_AUTHORIZATION")),
)


def professional_review_packets(request: StartupPlanIn, today: date) -> list[dict]:
    from fastapi import HTTPException

    packets = []
    seen = set()
    for item in request.professional_review:
        identity = (item.route, item.topic)
        if identity in seen or any(fact.observed_on > today for fact in item.facts):
            raise HTTPException(422, "Review packets need distinct route/topic pairs and non-future fact dates")
        seen.add(identity)
        jurisdiction = {
            "MANITOBA": "Manitoba", "FEDERAL_CANADA": "Canada (federal)",
            "INTERNATIONAL_FIRST": request.international_jurisdiction,
        }[item.route]
        packets.append({
            "route": item.route, "jurisdiction": jurisdiction, "topic": item.topic,
            "facts": [{**fact.model_dump(mode="json"), "basis": "OWNER_REPORTED"} for fact in item.facts],
            "questions": item.questions, "status": "DRAFT_AWAITING_QUALIFIED_REVIEW",
            "professional_signoff": None, "opinion_reference": None, "reliance_authorized": False,
        })
    return packets


def prepare_startup(request: StartupPlanIn, *, today=None):
    from app.services.startup_dependencies import startup_dependency_checklist

    today = today or datetime.now(timezone.utc).date()
    return {
        "currency": "CAD", "as_of": today.isoformat(),
        "funded_infrastructure": [item.model_dump() for item in request.funded_infrastructure],
        "owner_reported_surplus_assets": [asset.model_dump() for asset in request.surplus_assets],
        "startup_cash_available_minor": request.startup_cash_available_minor,
        "options": [compare_route(route, request, today) for route in ("MANITOBA", "FEDERAL_CANADA", "INTERNATIONAL_FIRST")],
        "cross_border_sources": [CORPORATE_RESIDENCY, DEPARTURE],
        "professional_review_packets": professional_review_packets(request, today),
        "checklist": [{"sequence": index, "step": step, "requires": requires}
                      for index, (step, requires) in enumerate(CHECKLIST, 1)],
        "startup_dependencies": startup_dependency_checklist(),
        "selected_jurisdiction": None, "activation_authorized": False, "external_effects": 0,
    }
