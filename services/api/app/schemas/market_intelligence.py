"""Inputs for owner-private market research and deterministic paper scenarios."""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

Currency = Literal["CAD", "USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD"]
Price = Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=8)]
Amount = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=8)]
Capital = Annotated[Decimal, Field(gt=0, le=1_000_000, max_digits=15, decimal_places=2)]
Bps = Annotated[int, Field(strict=True, ge=0, le=2500)]
Symbol = Annotated[str, Field(pattern=r"^[A-Z0-9][A-Z0-9.:-]{0,23}$")]
SourceRef = Annotated[str, Field(min_length=3, max_length=240)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class MarketScope(StrictModel):
    legacy_instance_id: str = Field(min_length=3, max_length=80)
    business_id: str = Field(min_length=3, max_length=120)
    engine_id: str = Field(min_length=3, max_length=80)
    jurisdiction: str = Field(min_length=2, max_length=80)


class Bar(StrictModel):
    at: AwareDatetime
    open: Price
    close: Price
    dividend: Amount = Decimal(0)


class Fundamentals(StrictModel):
    available_at: AwareDatetime
    earnings_per_share: Decimal | None = Field(None, max_digits=18, decimal_places=8)
    annual_distribution: Amount | None = None
    fund_expense_ratio_bp: Bps | None = None
    bond_yield_bp: Bps | None = None
    duration_years: Amount | None = None


class SecurityBatch(StrictModel):
    kind: Literal["SECURITY"]
    symbol: Symbol
    asset_class: Literal["STOCK", "ETF", "BOND"]
    currency: Currency
    sector: str = Field(min_length=1, max_length=60)
    price_basis: Literal["UNADJUSTED_SPLIT_FREE"]
    fundamentals: Fundamentals | None = None
    bars: list[Bar] = Field(min_length=4, max_length=366)

    @model_validator(mode="after")
    def chronological_bars(self):
        if any(a.at >= b.at or a.at.date() >= b.at.date() for a, b in zip(self.bars, self.bars[1:])):
            raise ValueError("Daily bars must be ordered and unique")
        if any(bar.at.utcoffset().total_seconds() != 0 for bar in self.bars):
            raise ValueError("Daily bars must use UTC")
        return self


class Quote(StrictModel):
    quote_id: UUID
    venue: str = Field(pattern=r"^[A-Z0-9][A-Z0-9_-]{1,39}$")
    base: Currency
    counter: Currency
    at: AwareDatetime
    expires_at: AwareDatetime
    bid: Price
    ask: Price
    bid_depth_base: Price
    ask_depth_base: Price
    fee_bp: Bps
    settlement_seconds: int = Field(strict=True, ge=0, le=604800)
    origin_ref: SourceRef

    @model_validator(mode="after")
    def valid_quote(self):
        if self.base == self.counter or self.bid > self.ask:
            raise ValueError("Quote currencies must differ and bid cannot exceed ask")
        if not 0 < (self.expires_at - self.at).total_seconds() <= 300:
            raise ValueError("Quote expiry must be within five minutes of observation")
        return self


class FXBatch(StrictModel):
    kind: Literal["FX"]
    quotes: list[Quote] = Field(min_length=1, max_length=60)

    @model_validator(mode="after")
    def distinct_quotes(self):
        if len({item.quote_id for item in self.quotes}) != len(self.quotes):
            raise ValueError("Quote IDs must be unique")
        return self


class MacroBatch(StrictModel):
    kind: Literal["MACRO"]
    topic: Literal["ECONOMIC_INDICATOR", "GOVERNMENT_POLICY", "CAPITAL_FLOW"]
    published_at: AwareDatetime
    summary: str = Field(min_length=3, max_length=2000)
    reported_measure: str = Field(min_length=1, max_length=120)


class MarketEvidenceIn(StrictModel):
    evidence_id: UUID
    scope: MarketScope
    source_id: str = Field(min_length=3, max_length=80)
    source_ref: SourceRef
    evidence_class: Literal["OPERATOR_REPORTED", "SIMULATION"]
    rights: Literal["AUTHORIZED_INTERNAL_RESEARCH"]
    data: Annotated[SecurityBatch | FXBatch | MacroBatch, Field(discriminator="kind")]


class Position(StrictModel):
    dataset_id: UUID
    weight_bp: int = Field(strict=True, gt=0, le=10000)


class InvestmentReplay(StrictModel):
    run_id: UUID
    scope: MarketScope
    as_of: AwareDatetime
    portfolio: list[Position] = Field(min_length=1, max_length=8)
    benchmark_id: UUID
    capital: Capital
    strategy: Literal["BUY_AND_HOLD", "CLOSE_ABOVE_MOVING_AVERAGE"]
    lookback: int = Field(default=3, strict=True, ge=2, le=100)
    half_spread_bp: Bps
    slippage_bp: Bps
    commission: Capital | Literal[0] = 0


class FXReplay(StrictModel):
    run_id: UUID
    scope: MarketScope
    as_of: AwareDatetime
    dataset_id: UUID
    mode: Literal["BEST_DIRECT", "CROSS_VENUE_LOOP", "TRIANGLE"]
    start_currency: Currency
    target_currency: Currency | None = None
    amount: Capital
    exposure_limit: Capital
    max_age_seconds: int = Field(strict=True, ge=1, le=60)
    max_settlement_seconds: int = Field(strict=True, ge=0, le=86400)
    slippage_bp: Bps
    failure_at_leg: int | None = Field(None, strict=True, ge=1, le=3)
    partial_fill_bp: int | None = Field(None, strict=True, ge=1, lt=10000)

    @model_validator(mode="after")
    def valid_scenario(self):
        legs = {"BEST_DIRECT": 1, "CROSS_VENUE_LOOP": 2, "TRIANGLE": 3}[self.mode]
        if self.mode == "BEST_DIRECT":
            if self.target_currency is None or self.target_currency == self.start_currency:
                raise ValueError("Direct conversion requires a different target currency")
        elif self.target_currency is not None:
            raise ValueError("An FX loop always returns to the starting currency")
        if self.amount > self.exposure_limit:
            raise ValueError("Starting amount exceeds exposure cap")
        if self.failure_at_leg is not None and self.failure_at_leg > legs:
            raise ValueError("Failure leg is outside route")
        if self.partial_fill_bp is not None and self.failure_at_leg is None:
            raise ValueError("Partial-fill scenario requires a failure leg")
        return self


class MarketForecastIn(StrictModel):
    forecast_id: UUID
    scope: MarketScope
    baseline_evidence_id: UUID
    outcome_source_id: str = Field(min_length=3, max_length=80)
    target_date: date
    threshold_close: Price
    probability_bp: int = Field(strict=True, ge=0, le=10000)
    cohort: Literal["PROSPECTIVE", "HOLDOUT"]


class MarketForecastResolution(StrictModel):
    outcome_evidence_id: UUID
