from uuid import UUID

from sqlalchemy.orm import Session

from app.god.models import GodReviewCase, GodReviewEvent
from app.loki.models import LokiFinding, LokiIndependentReceipt, LokiReconsideration, LokiReview
from app.models.god_verdicts import GodVerdict
from app.models.governance_decision import GovernanceDecision


ROOT = "/api/completion/phase3/universal-opportunity"


def test_independent_receipt_binds_findings_and_owner_reconsideration_to_prime_decision(deal_client, monkeypatch):
    client, engine = deal_client
    for model in (LokiReview, LokiFinding, LokiIndependentReceipt, LokiReconsideration,
                  GodReviewCase, GodReviewEvent, GodVerdict, GovernanceDecision):
        model.__table__.create(engine)

    reviewer_key = "isolated-independent-key"
    owner_key = "isolated-owner-mandate-key"
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_KEY", reviewer_key)
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_ID", "isolated-independent-reviewer")
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner_key)
    worker = {"X-Loki-Reviewer-Key": reviewer_key}
    owner = {"X-Owner-Mandate-Key": owner_key}
    opportunity = {
        "opportunity_id": "isolated-loki-01", "engine_id": "micro_saas",
        "legacy": "test-legacy", "jurisdiction": "CA-MB",
        "title": "Review case", "summary": "An internally evaluated proposal.",
    }

    def evaluate(candidate):
        return client.post(f"{ROOT}/evaluate", json={"shadow_mode": False, "opportunities": [candidate]})

    assert evaluate(opportunity).status_code == 409
    artifact = client.post(f"{ROOT}/review-artifact", json=opportunity).json()
    queued = client.post("/loki/reviews", json={**artifact, "input_source": "test-prime"})
    assert queued.status_code == 201, queued.text
    review_id = queued.json()["id"]
    assert queued.json()["status"] == "queued"
    assert client.post("/loki/reviews", json={**artifact, "input_source": "duplicate"}).json()["id"] == review_id
    assert client.get("/loki/worker/reviews").status_code == 401
    item = client.get("/loki/worker/reviews", headers=worker).json()[0]
    assert item["artifact_sha256"] == artifact["artifact_sha256"]
    assert item["raw_input"] == artifact["raw_input"]

    result = {
        "artifact_sha256": item["artifact_sha256"], "analysis_ref": "isolated-evidence:01",
        "summary": "Challenger documented a potential material assumption.",
        "findings": [{
            "category": "unit_economics", "severity": "warn", "material": True,
            "message": "Verify the renewal assumption.", "evidence_ref": "isolated-evidence:renewals",
        }],
    }
    path = f"/loki/worker/reviews/{review_id}/result"
    assert client.post(path, json=result).status_code == 401
    assert client.post(path, json=result, headers={"X-Loki-Reviewer-Key": owner_key}).status_code == 401
    with monkeypatch.context() as colliding:
        colliding.setenv("VALHALLA_SPECIALIST_GROQ_KEY", reviewer_key)
        assert client.post(path, json=result, headers=worker).status_code == 503
    assert client.post(path, headers=worker, json={**result, "artifact_sha256": "a" * 64}).status_code == 409
    response = client.post(path, json=result, headers=worker)
    assert response.status_code == 201, response.text
    assert client.post(path, json=result, headers=worker).status_code == 409

    reviewed = {**opportunity, "independent_loki_review_id": review_id}
    denied = evaluate(reviewed)
    assert denied.status_code == 409
    assert denied.json()["detail"]["verdict"]["reconsideration_status"] == "required"
    listing = client.get(f"/loki/reviews/{review_id}/findings")
    finding_id = listing.json()[0]["id"]
    acknowledgement = {
        "artifact_sha256": item["artifact_sha256"],
        "disposition": "accept_risk", "material_finding_ids": [finding_id],
        "reason": "Owner reconsidered the renewal assumption and retained an internal research scope.",
    }
    reconsider = f"/loki/reviews/{review_id}/reconsider"
    assert client.post(reconsider, json=acknowledgement).status_code == 401
    assert client.post(reconsider, headers=owner, json={**acknowledgement, "material_finding_ids": []}).status_code == 422
    accepted = client.post(reconsider, headers=owner, json=acknowledgement)
    assert accepted.status_code == 200, accepted.text
    assert evaluate({**reviewed, "summary": "Material version change."}).status_code == 409
    evaluated = evaluate(reviewed)
    assert evaluated.status_code == 200, evaluated.text
    evaluations = evaluated.json()["evaluations"]
    assert evaluations[0]["independent_loki"]["reconsideration_status"] == "accept_risk"
    assert evaluations[0]["independent_loki"]["external_effects_authorized"] is False
    assert evaluations[0]["independent_loki"]["reconsideration_sha256"] == accepted.json()["reconsideration_sha256"]
    with Session(engine) as db:
        receipt = db.get(LokiIndependentReceipt, UUID(review_id))
        assert receipt.reviewer_id == "isolated-independent-reviewer"
        assert db.get(LokiReconsideration, UUID(review_id)).material_finding_ids == [finding_id]
        review_case = db.query(GodReviewCase).one()
        assert review_case.heimdall_payload["result"]["independent_loki"]["review_id"] == review_id

        finding = db.get(LokiFinding, UUID(finding_id))
        finding.message = "An alteration to the already accepted findings."
        db.commit()
    assert client.get(f"/loki/reviews/{review_id}/findings").status_code == 409
    assert evaluate(reviewed).status_code == 409
    # A self-consistent replacement receipt still differs from the one accepted by the owner.
    from app.loki.review_service import result_digest

    with Session(engine) as db:
        review = db.get(LokiReview, UUID(review_id))
        receipt = db.get(LokiIndependentReceipt, UUID(review_id))
        receipt.result_sha256 = result_digest(review, receipt, review.findings)
        db.commit()
    refused = client.get(f"/loki/reviews/{review_id}/verdict")
    assert refused.status_code == 409
    assert "Owner disposition" in refused.json()["detail"]
    assert evaluate(reviewed).status_code == 409
    with Session(engine) as db:
        disposition = db.get(LokiReconsideration, UUID(review_id))
        disposition.decision_sha256 = None
        db.commit()
    assert evaluate(reviewed).status_code == 409
    with Session(engine) as db:
        receipt = db.get(LokiIndependentReceipt, UUID(review_id))
        receipt.result_sha256 = None
        db.commit()
    assert client.get(f"/loki/reviews/{review_id}").status_code == 200
    assert client.get(f"/loki/reviews/{review_id}/findings").status_code == 409
    assert client.get(f"/loki/reviews/{review_id}/verdict").status_code == 409
    assert evaluate(reviewed).status_code == 409


    critical_artifact = client.post(f"{ROOT}/review-artifact", json={
        **opportunity, "summary": "Separate version with a critical finding.",
    }).json()
    critical_id = client.post("/loki/reviews", json={**critical_artifact, "input_source": "test-prime"}).json()["id"]
    critical_result = {
        **result, "artifact_sha256": critical_artifact["artifact_sha256"],
        "findings": [{**result["findings"][0], "severity": "critical", "material": False}],
    }
    assert client.post(f"/loki/worker/reviews/{critical_id}/result", headers=worker, json=critical_result).status_code == 201
    critical_finding = client.get(f"/loki/reviews/{critical_id}/findings").json()[0]
    attempt = {
        **acknowledgement, "artifact_sha256": critical_artifact["artifact_sha256"],
        "material_finding_ids": [critical_finding["id"]],
    }
    assert client.post(f"/loki/reviews/{critical_id}/reconsider", headers=owner, json=attempt).status_code == 409
    assert client.post(f"/loki/reviews/{critical_id}/reconsider", headers=owner, json={
        **attempt, "disposition": "revise",
    }).status_code == 200
    assert client.get(f"/loki/reviews/{critical_id}/verdict").json()["ok_to_proceed"] is False


def test_local_analyst_process_publishes_material_and_hash_bound_findings(deal_client, loopback_api, monkeypatch):
    from pathlib import Path
    import runpy

    client, engine = deal_client
    for model in (LokiReview, LokiFinding, LokiIndependentReceipt, LokiReconsideration,
                  GodReviewCase, GodReviewEvent, GodVerdict, GovernanceDecision):
        model.__table__.create(engine)
    key = "local-loki-independent-fixture"
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_KEY", key)
    monkeypatch.setenv("VALHALLA_LOKI_REVIEWER_ID", "isolated-running-analyst")
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "isolated-reconsideration-owner")
    owner = {"X-Owner-Mandate-Key": "isolated-reconsideration-owner"}
    worker_root = Path(__file__).resolve().parents[1] / "tools" / "cron"
    monkeypatch.syspath_prepend(str(worker_root))
    worker = runpy.run_path(str(worker_root / "loki_analyst_worker.py"))["tick"]
    proposal = {
        "opportunity_id": "loki-autonomous-risk", "engine_id": "micro_saas", "legacy": "test-legacy",
        "jurisdiction": "CA-MB", "title": "Prospective test", "summary": "An internal proposal with cost exposure.",
        "estimated_test_cost": 20, "maximum_capital_exposure": 10, "available_safe_capital": 10,
    }
    artifact = client.post(f"{ROOT}/review-artifact", json=proposal).json()
    review = client.post("/loki/reviews", json={**artifact, "input_source": "isolated-local-process"}).json()
    loopback_api.headers.clear()
    loopback_api.headers["X-Loki-Reviewer-Key"] = key
    observed = worker(loopback_api, "universal_opportunity", "isolated-running-analyst")
    assert observed["status"] == "reviewed" and observed["verified"] is True
    assert observed["review_id"] == review["id"]
    assert observed["artifact_sha256"] == artifact["artifact_sha256"]
    assert observed["reviewer_id"] == "isolated-running-analyst"
    assert worker(loopback_api, "universal_opportunity", "isolated-running-analyst") == {"status": "idle"}
    assert loopback_api.get(f"/loki/reviews/{review['id']}").status_code == 401

    findings = client.get(f"/loki/reviews/{review['id']}/findings").json()
    assert any(item["severity"] == "critical" and item["tags"]["evidence_ref"] == "artifact:/estimated_test_cost"
               for item in findings)
    verdict_url = f"/loki/reviews/{review['id']}/verdict"
    verdict = client.get(verdict_url).json()
    assert verdict["ok_to_proceed"] is False
    assert verdict["reconsideration_status"] == "required"
    request = {"artifact_sha256": artifact["artifact_sha256"], "material_finding_ids": [item["id"] for item in findings],
               "disposition": "accept_risk", "reason": "Attempt to override the hard stop."}
    assert client.post(f"/loki/reviews/{review['id']}/reconsider", json=request, headers=owner).status_code == 409
    with Session(engine) as db:
        receipt = db.get(LokiIndependentReceipt, UUID(review["id"]))
        assert receipt.reviewer_id == "isolated-running-analyst"
        assert receipt.result_sha256 == observed["result_sha256"]
        db.get(LokiFinding, UUID(findings[0]["id"])).message = "Altered after publication"
        db.commit()
    assert client.get(verdict_url).status_code == 409


def test_local_analyst_retains_material_findings_for_unbound_specialist_claims():
    from app.loki.analyst import challenge
    from app.loki.evidence import artifact_digest

    kind, reference = "pantheon_report", "specialist-integrity"
    report = {
        "status": "observed",
        "external_authority": False,
        "observations": {
            "market_intelligence": ["malformed source"],
            "economic_reassessment": {
                "verified_performance_claim": {
                    "basis": "ECONOMIC_PERFORMANCE_FIXTURE",
                    "evidence_scope": "ECONOMIC_PERFORMANCE_FIXTURE_ONLY",
                    "record_id": "performance-fixture",
                    "period_net_minor": 250,
                    "verified_real_world_outcome": False,
                },
            },
            "treasury_statement_evidence": {"accounts": [], "actual_accessible_funds_minor": 250},
        },
    }
    review = challenge({
        "artifact_type": kind, "reference": reference, "raw_input": report,
        "artifact_sha256": artifact_digest(kind, reference, report),
    })
    by_category = {item.category: item for item in review.findings if item.material and item.severity == "critical"}
    assert {key: item.evidence_ref for key, item in by_category.items()} == {
        "market_simulation": "artifact:/observations/market_intelligence",
        "economic_fixture_contradiction": "artifact:/observations/economic_reassessment",
        "treasury_statement_conflict": "artifact:/observations/treasury_statement_evidence",
    }


def test_independent_worker_rejects_mismatched_publication_receipts(monkeypatch):
    from pathlib import Path
    import runpy
    from uuid import uuid4

    import httpx
    import pytest

    from app.loki.analyst import challenge
    from app.loki.evidence import artifact_digest

    worker_root = Path(__file__).resolve().parents[1] / "tools" / "cron"
    monkeypatch.syspath_prepend(str(worker_root))
    worker = runpy.run_path(str(worker_root / "loki_analyst_worker.py"))["tick"]
    kind = "pantheon_report"
    proposal = {"status": "observed", "external_authority": False, "observations": {}}
    item = {"artifact_type": kind, "reference": "fixture", "review_id": str(uuid4()), "raw_input": proposal,
            "artifact_sha256": artifact_digest(kind, "fixture", proposal)}
    receipt = {"review_id": item["review_id"], "artifact_sha256": item["artifact_sha256"],
               "result_sha256": "e" * 64, "analysis_ref": challenge(item).analysis_ref, "reviewer_id": "expected"}

    def run(overrides, status=201):
        def send(request):
            if request.method == "GET":
                return httpx.Response(200, json=[item])
            return httpx.Response(status, json={**receipt, **overrides})
        with httpx.Client(base_url="https://fixture.invalid", transport=httpx.MockTransport(send)) as client:
            return worker(client, kind, "expected")

    for changes in ({"review_id": str(uuid4())}, {"artifact_sha256": "f" * 64},
                    {"reviewer_id": "another"}, {"analysis_ref": "another"}, {"result_sha256": "malformed"}):
        with pytest.raises(RuntimeError, match="does not match"):
            run(changes)
    with pytest.raises(RuntimeError, match="does not match"):
        run({}, status=200)
    assert run({}, status=409) == {"status": "blocked", "verified": False}
