from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.services.wealth_scenario import (
    DEFAULT_PERSONAL_ANCHORS, PersonalAllocationIn, allocation_waterfall, interpolate_personal,
)


def inputs(**overrides):
    return PersonalAllocationIn.model_validate({
        "scope": {"legacy_instance_id": "test-legacy", "business_id": "test-business",
                  "engine_id": "test-engine", "jurisdiction": "CA-MB"},
        "statement_id": uuid4(), "essential_household_minor": 320000, "other_household_income_minor": 20000,
        "personal_reserve_target_minor": 700000, "personal_reserve_balance_minor": 500000,
        "operating_reserve_minor": 0, "corporate_tax_reserve_minor": 0, **overrides,
    })


def test_owner_anchors_are_continuous_and_conserve_eligible_capital():
    policy = inputs()
    assert interpolate_personal(0, policy.anchors) == 0
    for profit, target in DEFAULT_PERSONAL_ANCHORS:
        assert interpolate_personal(profit, policy.anchors) == target
        assert target - 1 <= interpolate_personal(profit - 1, policy.anchors) <= target
        assert target <= interpolate_personal(profit + 1, policy.anchors) <= target + 1
    assert interpolate_personal(1_750_000, policy.anchors) == 575_000
    assert interpolate_personal(1_000_000_000, policy.anchors) == 25_000_000
    with pytest.raises(ValidationError):
        inputs(anchors=[{"profit_minor":100,"personal_minor":80},{"profit_minor":110,"personal_minor":100}])


def test_household_and_reserve_share_one_capped_personal_allocation():
    policy = inputs(owner_monthly_limit_minor=350000)
    result = allocation_waterfall(1000000, policy)
    assert result["recommended_personal_minor"] == 350000
    assert result["personal_breakdown"] == {"essentials_minor":300000, "reserve_minor":50000, "remaining_personal_minor":0}
    assert result["remaining_eligible_for_reinvestment_minor"] == 650000
    assert result["shortfalls"] == {"essentials_minor":0, "personal_reserve_minor":150000}
    assert allocation_waterfall(0, policy)["contingency_review_recommended"] is True


def test_reverse_allocation_uses_first_sufficient_cent_and_respects_policy_ceiling():
    from app.services.commercial_targets import required_distributable_profit

    policy = inputs()
    for target in (1, 400000, 400001, 750001, 1250000, 25000000):
        profit = required_distributable_profit(target, policy)
        assert interpolate_personal(profit - 1, policy.anchors) < target
        assert interpolate_personal(profit, policy.anchors) >= target
    assert required_distributable_profit(25000001, policy) is None
    assert required_distributable_profit(350001, inputs(owner_monthly_limit_minor=350000)) is None
