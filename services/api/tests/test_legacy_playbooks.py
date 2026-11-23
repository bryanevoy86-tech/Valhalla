from datetime import datetime, timedelta, timezone
import json

from sqlalchemy.orm import Session

from app.models.completion_registry import (
    LegacyGovernancePolicy, LegacyInstancePolicyState, LegacyInstanceRegistryItem, LegacyOrchestrationEvent,
)


ROOT = "/api/prime/legacy-playbooks"


def test_clone_and_regional_mirror_have_distinct_reproducible_registry_receipts(deal_client, monkeypatch):
    client, engine = deal_client
    owner = {"X-Owner-Mandate-Key": "isolated-legacy-playbook-owner"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    for model in (LegacyGovernancePolicy, LegacyInstancePolicyState, LegacyInstanceRegistryItem, LegacyOrchestrationEvent):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(LegacyGovernancePolicy(
            policy_id="primary", policy_scope="GLOBAL", policy_version="v4",
            autonomy_policy_json="{}", ethics_evidence_policy_json="{}", kill_shield_policy_json="{}",
            engine_activation_policy_json="{}", jurisdiction_restrictions_json="{}",
            approval_requirements_json="{}", audit_requirements_json="{}",
        ))
        db.add(LegacyInstancePolicyState(legacy_instance_id="original", policy_id="primary", policy_version="v4"))
        db.add(LegacyInstanceRegistryItem(
            legacy_instance_id="original", display_name="Original", synchronization_status="SYNCED", status="PASS",
            assigned_businesses_json='["original-biz"]', assigned_jurisdictions_json='["CA-MB"]',
            local_knowledge_context_json=json.dumps({
                "business_id": "original-biz", "jurisdiction": "CA-MB", "data_namespace": "original-private",
                "governance": {"policy_id": "primary", "policy_version": "v4"},
                "local_knowledge_refs": ["fixture:private-source"],
            }),
            engines_json='["micro_saas"]', permissions_json='{"external":true}',
            integrations_json='{"fixture_secret":"must-not-copy"}',
        ))
        db.commit()

    clone = {
        "kind": "BUSINESS_CLONE", "source_legacy_id": "original", "source_business_id": "original-biz",
        "source_jurisdiction": "CA-MB", "target_legacy_id": "cloned",
        "target_business_id": "cloned-biz", "target_jurisdiction": "CA-MB",
        "target_display_name": "Cloned business", "engine_id": "micro_saas",
    }
    mirror = {
        **clone, "kind": "REGIONAL_MIRROR", "target_legacy_id": "mirror",
        "target_business_id": "original-biz", "target_jurisdiction": "CA-ON",
    }
    assert client.post(ROOT, json=clone).status_code == 401
    for bad in (
        {**clone, "target_business_id": "original-biz"},
        {**mirror, "target_business_id": "another-biz"},
        {**mirror, "target_jurisdiction": "CA-MB"},
    ):
        assert client.post(ROOT, json=bad, headers=owner).status_code == 422
    assert client.post(ROOT, json={**clone, "engine_id": "unassigned"}, headers=owner).status_code == 409

    records = []
    for request in (clone, mirror):
        response = client.post(ROOT, json=request, headers=owner)
        assert response.status_code == 201, response.text
        record = response.json()
        records.append(record)
        assert record["status"] == "REGISTRY_REHEARSED"
        assert record["source_governance"]["policy_version"] == "v4"
        assert record["external_authority"] is False
        assert record["live_traffic_routed"] is False
        assert client.post(ROOT, json=request, headers=owner).json() == record
        assert client.get(f"{ROOT}/{request['target_legacy_id']}").json() == record
    assert records[0]["target_namespace"] != records[1]["target_namespace"]
    assert "INDEPENDENT_BUSINESS_PLAYBOOK_REVIEW" in records[0]["required_evidence"]
    assert "REGIONAL_REPLICATION_AND_FAILOVER_PROOF" in records[1]["required_evidence"]
    assert client.post(ROOT, json={**clone, "target_display_name": "Changed"}, headers=owner).status_code == 409

    with Session(engine) as db:
        assert db.query(LegacyOrchestrationEvent).count() == 2
        assert db.query(LegacyInstancePolicyState).count() == 1
        for target in db.query(LegacyInstanceRegistryItem).filter(LegacyInstanceRegistryItem.legacy_instance_id != "original"):
            assert target.status == "EXTERNAL_OWNER_ACTION_REQUIRED"
            assert target.synchronization_status == "PENDING"
            assert target.permissions_json == "{}"
            assert target.integrations_json == "{}"
            assert target.engines_json == "[]"
            assert "local_knowledge_refs" not in json.loads(target.local_knowledge_context_json)


    from app.models.completion_registry import LegacyInstanceWorkItem
    from app.models.media_engine import MediaContent

    for model in (LegacyInstanceWorkItem, MediaContent):
        model.__table__.create(engine, checkfirst=True)
    scope = {"legacy_instance_id": "original", "business_id": "original-biz", "jurisdiction": "CA-MB",
             "engine_id": "micro_saas"}
    outcome = "MIMIR-" + "a" * 64
    observation = {"outcome_event_id": outcome, "artifact_sha256": "b" * 64,
                   "sales_verified": False, "observed_at": datetime.now(timezone.utc).isoformat()}

    def outcomes(db, *, trigger_event_id, limit, **requested_scope):
        return [observation.copy()] if requested_scope == scope and trigger_event_id == outcome else []

    monkeypatch.setattr("app.routers.legacy_playbooks.verified_internal_outcomes", outcomes)
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "0")
    request = {"scope": scope, "name": "build-draft", "version": 1, "outcome_ids": [outcome],
               "input_contract": ["Approved research packet"], "acceptance_checks": ["Exact artifact digest"],
               "rollback_procedure": "Discard the unpublished draft and retain the approved prior version.",
               "data_class": "SYNTHETIC"}
    record_url, assess_url = ROOT + "/workflow-versions/record", ROOT + "/workflow-versions/assess"
    assert client.post(record_url, json=request).status_code == 401
    assert client.post(record_url, json={**request, "outcome_ids": ["MIMIR-" + "c" * 64]}, headers=owner).status_code == 409
    registered = client.post(record_url, json=request, headers=owner)
    assert registered.status_code == 201, registered.text
    first = registered.json()
    assert client.post(record_url, json=request, headers=owner).json() == first
    assert client.post(record_url, json={**request, "acceptance_checks": ["Changed"]}, headers=owner).status_code == 409
    assess = {"source": scope, "target": scope, "name": request["name"], "version": 1,
              "expected_sha256": first["sha256"], "data_class": "SYNTHETIC"}
    candidate = client.post(assess_url, json=assess).json()
    assert candidate["status"] == "DETERMINISTIC_CANDIDATE" and candidate["execution_authorized"] is False
    cross = client.post(assess_url, json={**assess, "target": {**scope, "jurisdiction": "CA-ON"}}).json()
    assert cross["review_reasons"] == ["CROSS_SCOPE_LOKI_AND_LOCAL_REVIEW_REQUIRED"]
    assert client.post(record_url, json={**request, "version": 2}, headers=owner).status_code == 409
    assert client.post(record_url, json={**request, "version": 2, "previous_sha256": first["sha256"]},
                       headers=owner).status_code == 201
    assert "WORKFLOW_SUPERSEDED" in client.post(assess_url, json=assess).json()["review_reasons"]
    observation["observed_at"] = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
    assert "SOURCE_EVIDENCE_POLICY_OR_CONTAINMENT_HOLD" in client.post(assess_url, json=assess).json()["review_reasons"]
