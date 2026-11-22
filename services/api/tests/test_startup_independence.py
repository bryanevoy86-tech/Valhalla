from datetime import date

from fastapi import HTTPException
import pytest
from pydantic import ValidationError

from app.services.startup_independence import StartupIndependenceIn, startup_independence


def plan(**overrides):
    return StartupIndependenceIn.model_validate({
        "registration_date": "2026-08-01", "registration_evidence_ref": "fixture:registration",
        "commissioning_date": "2026-09-22", "completed_reviews": [15],
        "monthly_essentials_minor": 120000, "reserve_months": 3, "reserve_balance_minor": 60000,
        "monthly_stretch_low_minor": 180000, "monthly_stretch_high_minor": 240000,
        "opening_unrestricted_cash_fixture_minor": 50000, "establishment_minor": 42000,
        "operating_minor": 15000, "business_reserve_minor": 8000, "experiment_minor": 2000,
        "hypothetical_extra_contributions_minor": [25000], "reporting_month": "2026-09-01",
        **overrides,
    })


def test_review_clock_uses_registration_even_when_commissioning_is_delayed():
    data = startup_independence(plan(), date(2026, 9, 30))
    assert data["reviews"][0] == {"day": 15, "due": "2026-08-16", "focus": "DEMAND_PROSPECTS_AND_PILOT_READINESS",
                                   "status": "OWNER_REPORTED_COMPLETE"}
    assert data["reviews"][3]["status"] == "REASSESS" and data["reviews"][-1]["due"] == "2026-10-30"
    assert data["personal_reserve_target_minor"] == 360000 and data["personal_reserve_gap_minor"] == 300000
    assert data["verified_after_tax_income_minor"] is None and data["household_estimated_shortfall_minor"] is None
    with pytest.raises(HTTPException):
        startup_independence(plan(completed_reviews=[90]), date(2026, 9, 30))


def test_unreceived_and_restricted_sources_do_not_fill_zero_contribution_gap():
    funding = [{"evidence_ref": f"fixture:{kind}", "kind": kind, "status": state, "amount_minor": 100000}
               for kind, state in (("GRANT", "APPROVED"), ("CREDIT", "RECEIVED"), ("REIMBURSEMENT", "REIMBURSABLE"),
                                   ("CUSTOMER_ADVANCE", "RESTRICTED"), ("LOAN", "RECEIVED"))]
    result = startup_independence(plan(funding=funding), date(2026, 9, 30))
    no_extra, hypothetical = result["capital_scenarios"]
    assert no_extra["hypothetical_extra_contribution_minor"] == 0 and no_extra["total_plan_gap_minor"] == 17000
    assert no_extra["experiment_headroom_minor"] == 0 and hypothetical["experiment_headroom_minor"] == 10000
    assert all(line["included_in_spendable_cash_minor"] == 0 for line in result["funding"])
    assert result["verified_available_cash_minor"] is None and result["borrowing_authorized"] is False


def test_reporting_retains_entries_and_keeps_owner_estimates_unverified():
    rows = [{"category": category, "amount_minor": amount, "evidence_ref": f"fixture:{category}",
             "occurred_on": "2026-09-02", "basis": "OWNER_REPORTED"}
            for category, amount in (("RETAINED_EARNINGS", 23700), ("PERSONAL_ASSET_SALE", 14000),
                                     ("GROSS_PERSONAL_COMPENSATION", 84000), ("PERSONAL_TAX", 22000),
                                     ("ASSISTANCE", 12000), ("GRANT", 18000), ("SUBSIDY", 4000))]
    result = startup_independence(plan(reporting_lines=rows, reporting_rules_ref="fixture:rules",
                                       reporting_rules_checked_on="2026-09-01"), date(2026, 9, 30))
    assert result["reporting"]["lines"] == rows
    assert result["owner_estimated_net_income_minor"] == 62000 and result["household_estimated_shortfall_minor"] == 46000
    assert result["verified_after_tax_income_minor"] is None and result["support_forecast_minor"] is None
    assert result["reporting"]["official_or_case_evidence_verified"] is False
    with pytest.raises(ValidationError, match="unique"):
        plan(reporting_lines=[rows[0], rows[0]])
