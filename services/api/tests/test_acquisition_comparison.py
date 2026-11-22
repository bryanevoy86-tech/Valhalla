from app.services.acquisition_comparison import compare_settled_campaigns


def settled(campaign, buyers, contribution, **overrides):
    return {"campaign_id": campaign, "sha256": str(campaign) * 64, "visits": 80,
            "positive_net_orders": buyers, "contribution_minor": contribution,
            "acquisition_cost_covered": True, "unresolved_orders": 0,
            "recorded_acquisition_cost_exceeds_budget": False, **overrides}


def test_profitable_distinguishable_campaign_goes_to_scale_review_and_loss_stops():
    profitable = settled(1, 45, 8000)
    loss = settled(2, 6, -900)
    arms = compare_settled_campaigns([profitable, loss], 40)
    assert [arm["decision"] for arm in arms] == ["SCALE_REVIEW", "STOP"]


def test_profitable_but_overlapping_conversion_intervals_continue_testing():
    arms = compare_settled_campaigns([settled(1, 24, 5400), settled(2, 23, 5200)], 40)
    assert all(arm["decision"] == "CONTINUE_TESTING" for arm in arms)
    assert all(arm["reason"] == "COMPARATIVE_EVIDENCE_INCONCLUSIVE" for arm in arms)


def test_cost_coverage_and_open_settlement_prevent_scale_review():
    arms = compare_settled_campaigns([settled(1, 40, 12000, acquisition_cost_covered=False),
                                     settled(2, 8, None, unresolved_orders=1)], 40)
    assert [arm["decision"] for arm in arms] == ["IMPROVE", "CONTINUE_TESTING"]
    limited = settled(3, 3, None, unresolved_orders=1, recorded_acquisition_cost_exceeds_budget=True)
    assert compare_settled_campaigns([limited, settled(2, 20, 2000)], 40)[0]["decision"] == "STOP"
