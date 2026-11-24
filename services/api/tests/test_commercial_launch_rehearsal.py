"""Evaluate CAD offer hypotheses through Prime and a separately keyed Loki worker."""
import json
from pathlib import Path
import runpy

from sqlalchemy.orm import Session

from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview
from app.models.completion_registry import KnowledgeRegistryItem, LearningFeedbackRecord
from app.loki.analyst import challenge
from app.loki.evidence import artifact_digest


ROOT = "/api/completion/phase3/universal-opportunity"
OFFER_CASES = (
    # ID, engine, title, per-unit CAD price, labour, tools/fees, reserve, CAC,
    # downside labour and CAC, cash budget, days, repeat model, evidence confidence.
    ("quote-setup", "ai_automation_services", "Exterior contractor quote-to-cash setup",
     1490, 480, 65, 75, 240, 840, 550, 150, 21, "SERVICE", 0.64),
    ("fleet-ops", "micro_saas", "Small-fleet maintenance operations",
     199, 60, 25, 10, 45, 120, 90, 250, 45, "SUBSCRIPTION", 0.55),
    ("workflow-studio", "ai_automation_services", "Cross-industry workflow implementation",
     2500, 1200, 125, 125, 450, 1800, 850, 200, 36, "SERVICE", 0.49),
    ("site-photo", "micro_saas", "Exterior progress photo and change-order evidence",
     249, 70, 40, 13, 55, 120, 100, 400, 60, "SUBSCRIPTION", 0.52),
    ("invoice-readiness", "ops_automation", "Invoice-readiness and receivables desk",
     349, 120, 35, 18, 65, 220, 120, 200, 35, "RECURRING", 0.51),
    ("supplier-watch", "market_intelligence", "Specialty material price watch",
     99, 35, 24, 5, 45, 60, 70, 400, 75, "SUBSCRIPTION", 0.27),
)


def _proposal(case):
    (key, engine, title, price, labour, tools, reserve, cac,
     stress_labour, stress_cac, cash, days, revenue, confidence) = case
    return {
        "opportunity_id": key, "engine_id": engine, "title": title,
        "legacy": "synthetic-commercial-scope", "jurisdiction": "CA-MB",
        "source": "public-benchmarks-plus-unverified-hypotheses",
        "summary": "Isolated prospective offer. Research only. No customer or provider action.",
        "persist_decision": False, "human_approval_required": True,
        "required_capital": cash, "estimated_test_cost": cash, "maximum_capital_exposure": cash,
        "available_safe_capital": 0,
        "estimated_time_to_first_revenue_days": days, "revenue_type": revenue,
        "expected_margin_low": (price - stress_labour - tools - reserve - stress_cac) / price,
        "expected_margin_high": (price - labour - tools - reserve - cac) / price,
        "scalability": 0.65 if revenue == "SERVICE" else 0.75,
        "strategic_value": 0.85 if key == "quote-setup" else 0.6,
        "evidence_confidence": confidence,
        "point_of_no_return": "Entering a customer agreement or paying for access",
        "exit_options": ["Stop before provisioning"],
        "specialist_inputs": {
            "commercial_validation": {
                "basis": "CAD_RESEARCH_HYPOTHESIS", "currency": "CAD",
                "verified_customer_outcomes": False, "external_action_authorized": False,
                "price_minor": price * 100, "labour_minor": labour * 100,
                "tools_and_fees_minor": tools * 100, "reserve_minor": reserve * 100,
                "acquisition_minor": cac * 100, "stress_labour_minor": stress_labour * 100,
                "stress_acquisition_minor": stress_cac * 100,
            },
        },
    }


def test_rank_and_independently_challenge_commercial_offers(deal_client, loopback_api, monkeypatch):
    client, engine = deal_client
    for model in (LokiReview, LokiFinding, LokiIndependentReceipt, LokiReconsideration, KnowledgeRegistryItem, LearningFeedbackRecord):
        model.__table__.create(engine)
    reviewer_id = "isolated-commercial-analyst"
    reviewer_key = "local-commercial-review-fixture"
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_KEY", reviewer_key)
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_ID", reviewer_id)
    worker_path = Path(__file__).resolve().parents[1] / "tools" / "cron" / "loki_analyst_worker.py"
    monkeypatch.syspath_prepend(str(worker_path.parent))
    tick = runpy.run_path(str(worker_path))["tick"]
    loopback_api.headers.clear()
    loopback_api.headers["X-Loki-Reviewer-Key"] = reviewer_key

    offers = [_proposal(case) for case in OFFER_CASES]
    response = client.post(f"{ROOT}/evaluate", json={
        "opportunities": offers, "shadow_mode": True, "persist_decision": False,
    })
    assert response.status_code == 200, response.text
    result = response.json()
    rows = result["evaluations"]
    assert len(rows) == len(offers)
    assert all(row["pantheon"]["external_effects_authorized"] is False for row in rows)
    by_id = {row["opportunity_id"]: row["rank_value"] for row in rows}
    assert by_id["invoice-readiness"] > by_id["supplier-watch"]

    receipts = []
    for offer in offers:
        response = client.post(f"{ROOT}/review-artifact", json=offer)
        assert response.status_code == 200, response.text
        artifact = response.json()
        response = client.post("/loki/reviews", json={**artifact, "input_source": "isolated-commercial-demo"})
        assert response.status_code == 201, response.text
        review_id = response.json()["id"]
        receipt = tick(loopback_api, "universal_opportunity", reviewer_id)
        assert receipt["verified"] is True and receipt["review_id"] == review_id
        assert receipt["artifact_sha256"] == artifact["artifact_sha256"]
        findings = client.get(f"/loki/reviews/{review_id}/findings").json()
        categories = {row["category"] for row in findings}
        assert {"customer_demand_unproven", "capital_limit", "source_verification_required"} <= categories
        expected = "commercial_base_loss" if offer["opportunity_id"] == "supplier-watch" else "commercial_stress_loss"
        assert expected in categories
        assert not client.get(f"/loki/reviews/{review_id}/verdict").json()["ok_to_proceed"]
        receipts.append({
            "opportunity": offer["opportunity_id"],
            "rank": by_id[offer["opportunity_id"]],
            "categories": sorted(categories),
            **receipt,
        })
    with Session(engine) as db:
        assert db.query(LokiIndependentReceipt).count() == len(offers)
    print("COMMERCIAL_REHEARSAL " + json.dumps({"receipts": receipts, "externally_authorized": False}))


def test_commercial_challenge_refuses_false_authority_and_invalid_costs():
    def review(case_changes):
        proposal = _proposal(OFFER_CASES[0])
        proposal["specialist_inputs"]["commercial_validation"].update(case_changes)
        kind = "universal_opportunity"
        reference = proposal["opportunity_id"]
        return challenge({
            "artifact_type": kind, "reference": reference, "raw_input": proposal,
            "artifact_sha256": artifact_digest(kind, reference, proposal),
        }).findings

    for changes, category in (
        ({"verified_customer_outcomes": True}, "commercial_authority_conflict"),
        ({"external_action_authorized": True}, "commercial_authority_conflict"),
        ({"acquisition_minor": True}, "commercial_cost_basis"),
        ({"stress_labour_minor": 5}, "commercial_cost_basis"),
    ):
        assert any(f.category == category and f.severity == "critical" for f in review(changes))
    assert not any(f.category == "commercial_stress_loss" for f in review({"price_minor": 300000}))
