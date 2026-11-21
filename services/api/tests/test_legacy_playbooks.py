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
