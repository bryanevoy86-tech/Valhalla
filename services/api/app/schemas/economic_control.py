"""Owner-private planning contracts. Financial inputs are rehearsal fixtures."""
from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.market_intelligence import MarketScope, StrictModel

Money = Annotated[int, Field(strict=True, ge=0, le=100_000_000_000)]
Net = Annotated[int, Field(strict=True, ge=-100_000_000_000, le=100_000_000_000)]
BP = Annotated[int, Field(strict=True, ge=0, le=10000)]
Reference = Annotated[str, Field(min_length=3, max_length=180)]
Currency = Literal["CAD", "USD", "EUR", "GBP"]
Advice = Literal["CONTINUE", "EXPAND", "IMPROVE", "SUSPEND", "RESTRUCTURE", "EXIT", "REDEPLOY", "RESTART"]


class Mandate(StrictModel):
    id: UUID
    scope: MarketScope
    currency: Currency
    previous_id: UUID | None = None
    max_exposure: Money
    max_cumulative_loss: Money
    max_additional_funding: Money
    min_operating_reserve: Money
    review_by: date
    opening_cumulative_loss: Money = 0
    opening_additional_funding: Money = 0
    opening_receipt_ref: Reference | None = None
    minimum_period_net: Net
    continuation_criteria: Reference
    suspension_criteria: Reference
    exit_criteria: Reference
    obligations: list[Reference] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def opening_history(self):
        if (self.opening_cumulative_loss or self.opening_additional_funding) and not self.opening_receipt_ref:
            raise ValueError("Opening economic history requires an accounting receipt reference")
        return self


class Performance(StrictModel):
    id: UUID
    scope: MarketScope
    start: date
    end: date
    operating_receipts: Money
    operating_costs: Money
    outstanding_exposure: Money
    uncommitted_local_cash: Money
    receipt_ref: Reference
    obligations_status: Literal["SATISFIED", "UNRESOLVED", "BREACHED"]
    evidence_class: Literal["RECONCILIATION_FIXTURE"]
    checkout_order_id: UUID | None = None
    checkout_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def period_order(self):
        if self.start > self.end:
            raise ValueError("Invalid reporting period")
        if (self.checkout_order_id is None) != (self.checkout_sha256 is None):
            raise ValueError("Checkout order ID and SHA-256 must be supplied together")
        if self.checkout_order_id is not None:
            if self.receipt_ref != f"checkout-fixture:{self.checkout_order_id}":
                raise ValueError("Checkout-linked performance requires the canonical order receipt reference")
        elif self.receipt_ref.casefold().startswith("checkout-fixture:"):
            raise ValueError("Reserved checkout receipt reference requires verified order evidence")
        return self

    def journal_payload(self):
        fields = {"checkout_order_id", "checkout_sha256"} if self.checkout_order_id is None else set()
        return self.model_dump(mode="json", exclude=fields)


class Liquidity(StrictModel):
    id: UUID
    scope: MarketScope
    receipt_ref: Reference
    as_of: date
    unrestricted_pool_minor: Money
    protected_pool_minor: Money
    evidence_class: Literal["RECONCILIATION_FIXTURE"]


class Opportunity(StrictModel):
    id: UUID
    scope: MarketScope
    opportunity_key: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{2,79}$")]
    replaces_id: UUID | None = None
    title: Reference
    origin: Literal["HISTORICAL_PLAYBOOK", "OPERATING_BUSINESS", "NEW_DISCOVERY", "FOUNDRY"]
    status: Literal["CANDIDATE", "OPERATING_REPORTED", "SUSPENDED", "REJECTED"]
    evidence_ref: Reference
    foundry_evidence_id: UUID | None = None
    valid_through: date
    required_capital: Money
    projected_annual_net: Net
    maximum_downside: Money
    uncertainty_bp: BP
    demand_bp: BP
    operational_independence_bp: BP
    time_to_revenue_days: Annotated[int, Field(strict=True, ge=0, le=730)]
    compliance: Literal["SATISFIED_IN_FIXTURE", "UNRESOLVED", "BLOCKED"]
    human_hours_weekly: Annotated[int, Field(strict=True, ge=0, le=168)] = 0
    unresolved_dependency_count: Annotated[int, Field(strict=True, ge=0, le=15)] = 0
    dependencies: list[Reference] = Field(max_length=15)
    activation_requirements: list[Reference] = Field(min_length=1, max_length=15)

    @model_validator(mode="after")
    def foundry_identity(self):
        if self.unresolved_dependency_count > len(self.dependencies):
            raise ValueError("Unresolved dependencies exceed declared dependencies")
        if (self.origin == "FOUNDRY") != (self.foundry_evidence_id is not None):
            raise ValueError("Foundry origin requires a Foundry evidence ID")
        return self


class RecoverableAsset(StrictModel):
    asset_ref: Reference
    kind: Literal["SOFTWARE", "KNOWLEDGE", "INFRASTRUCTURE", "EQUIPMENT", "OTHER"]
    rights: Literal["REUSE_PERMITTED", "REVIEW_REQUIRED", "ENCUMBERED"]
    projected_liquidation_minor: Money
    obligations: list[Reference] = Field(max_length=12)


class Plan(StrictModel):
    id: UUID
    scope: MarketScope
    action: Advice
    requested_additional_minor: Money
    alternative_key: str | None = Field(None, pattern=r"^[a-z][a-z0-9_-]{2,79}$")
    rationale: Annotated[str, Field(min_length=5, max_length=750)]
    past_spend_minor: Money
    cross_business_support: bool = False
    assets: list[RecoverableAsset] = Field(max_length=20)

    @model_validator(mode="after")
    def action_fields(self):
        if (self.action == "REDEPLOY") != bool(self.alternative_key):
            raise ValueError("Redeployment alone requires a scoped alternative")
        if self.action in {"EXIT", "SUSPEND", "CONTINUE", "RESTRUCTURE", "RESTART"} and self.requested_additional_minor:
            raise ValueError("This action cannot request new exposure")
        if len({asset.asset_ref for asset in self.assets}) != len(self.assets):
            raise ValueError("Recoverable asset references must be unique")
        return self


class Decision(StrictModel):
    plan: Plan
    independent_review_id: UUID
    expected_artifact_sha256: Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Containment(StrictModel):
    id: UUID
    scope: MarketScope
    rationale: Annotated[str, Field(min_length=5, max_length=750)]


class ReservationRelease(StrictModel):
    id: UUID
    scope: MarketScope
    decision_id: UUID
    reason: Literal["CANCELLED", "EXPIRED", "PLAN_REPLACED"]
    evidence_ref: Reference


class Obligation(StrictModel):
    id: UUID
    scope: MarketScope
    obligation_key: Reference
    previous_id: UUID | None = None
    due_on: date
    amount_minor: Money
    status: Literal["OPEN", "DISPUTED", "CLOSED_IN_FIXTURE"]
    evidence_ref: Reference


class AssetRecovery(StrictModel):
    id: UUID
    scope: MarketScope
    exit_decision_id: UUID
    asset_ref: Reference
    statement_id: UUID
    entry_ref: Reference
