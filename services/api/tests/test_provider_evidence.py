from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.model_provider import ModelProvider
from app.models.provider_evidence import ProviderEvidence


def test_provider_comparison_scopes_synthetic_evidence_and_separates_loki(deal_client, monkeypatch):
    client, engine = deal_client
    root = "/api/prime/provider-intelligence"
    owner = {"X-Owner-Mandate-Key": "fixture-provider-review"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    for model in (ModelProvider, ProviderEvidence):
        model.__table__.create(engine)
    with Session(engine) as db:
        prime = ModelProvider(name="prime-fixture", vendor="openai", active=True, default_for_heimdall=True,
                              config={"model": "prime-fixture", "opaque_setting": "fixture-do-not-expose"})
        challenger = ModelProvider(name="loki-fixture", vendor="groq", active=True, default_for_heimdall=False,
                                   config={"model": "loki-fixture"})
        db.add_all([prime, challenger])
        db.commit()
        prime_id, challenger_id = prime.id, challenger.id

    assert client.get(f"{root}/suite").json()["provider_call_authorized"] is False
    data = {
        "evidence_id": str(uuid4()), "provider_id": prime_id, "role": "LOKI",
        "evidence_class": "OWNER_SUPPLIED_SYNTHETIC",
        "answers": {"private_document": "BLOCK", "missing_evidence": "ABSTAIN",
                    "material_objection": "REVIEW", "synthetic_summary": "ADVISE"},
    }
    assert client.post(f"{root}/evidence", json=data).status_code == 401
    first = client.post(f"{root}/evidence", json=data, headers=owner)
    assert first.status_code == 201, first.text
    assert first.json()["score"] == 1
    assert "fixture-do-not-expose" not in first.text
    assert client.get(f"{root}/recommendations", params={"role": "LOKI", "data_class": "SYNTHETIC"}).json()["candidates"] == []

    second_data = {**data, "evidence_id": str(uuid4()), "provider_id": challenger_id}
    second = client.post(f"{root}/evidence", json=second_data, headers=owner)
    assert second.status_code == 201, second.text
    assert client.post(f"{root}/evidence", json=second_data, headers=owner).json() == second.json()
    assert client.post(f"{root}/evidence", json={**second_data, "role": "BRAGI"}, headers=owner).status_code == 409
    assert client.get(f"{root}/recommendations", params={"role": "LOKI"}).json()["candidates"] == []
    candidate = client.get(f"{root}/recommendations", params={"role": "LOKI", "data_class": "SYNTHETIC"}).json()
    assert [row["provider_id"] for row in candidate["candidates"]] == [challenger_id]
    assert candidate["candidates"][0]["provider_provenance_verified"] is False
    assert candidate["automatic_selection"] is False

    with Session(engine) as db:
        db.get(ModelProvider, challenger_id).config = {"model": "another-model"}
        db.commit()
    assert client.get(f"{root}/recommendations", params={"role": "LOKI", "data_class": "SYNTHETIC"}).json()["candidates"] == []


def test_specialist_stage_probe_is_metered_fixed_synthetic_and_independently_configured(deal_client, monkeypatch):
    import httpx
    from app.models.go_live_state import GoLiveState
    from app.models.owner_conversation import OwnerInferenceAttempt, OwnerInferenceQuota
    from app.models.specialist_probe import SpecialistProbe
    from app.routers import specialist_probes

    client, engine = deal_client
    root = "/api/prime/provider-intelligence"
    owner = {"X-Owner-Mandate-Key": "fixture-specialist-owner"}
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", owner["X-Owner-Mandate-Key"])
    monkeypatch.delenv("VALHALLA_SPECIALIST_STAGING_AUTHORIZED", raising=False)
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    for model in (ModelProvider, ProviderEvidence, OwnerInferenceQuota, OwnerInferenceAttempt, GoLiveState, SpecialistProbe):
        model.__table__.create(engine)
    with Session(engine) as db:
        prime = ModelProvider(name="prime-fixture", vendor="openai", active=True, default_for_heimdall=True,
                              config={"model": "prime-fixture"})
        challenger = ModelProvider(name="loki-fixture", vendor="groq", active=True, default_for_heimdall=False,
                                   config={"model": "loki-fixture"})
        db.add_all([prime, challenger, GoLiveState(id=1, go_live_enabled=False, kill_switch_engaged=False)])
        db.commit()
        challenger_id = challenger.id
    evidence = {
        "evidence_id": str(uuid4()), "provider_id": challenger_id, "role": "LOKI",
        "evidence_class": "OWNER_SUPPLIED_SYNTHETIC",
        "answers": {"private_document": "BLOCK", "missing_evidence": "ABSTAIN",
                    "material_objection": "REVIEW", "synthetic_summary": "ADVISE"},
    }
    assert client.post(f"{root}/evidence", json=evidence, headers=owner).status_code == 201

    # Patch the router's module reference instead of the HTTP test client's transport.
    from types import SimpleNamespace
    calls = []
    class FakeHTTP:
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False and kwargs["trust_env"] is False
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, **kwargs):
            calls.append((url, kwargs))
            if len(calls) == 2:
                return httpx.Response(429, request=httpx.Request("POST", url))
            return httpx.Response(200, request=httpx.Request("POST", url), json={
                "choices": [{"finish_reason": "stop", "message": {"content": "REVIEW"}}],
                "usage": {"prompt_tokens": 42, "completion_tokens": 1},
            })
    monkeypatch.setattr(specialist_probes, "httpx", SimpleNamespace(Client=FakeHTTP, HTTPError=httpx.HTTPError))
    probe = {"probe_id": str(uuid4()), "role": "LOKI", "provider_id": challenger_id, "case_id": "material_objection"}
    assert client.post(f"{root}/stage-probes", json=probe, headers=owner).status_code == 503
    for key, value in {
        "VALHALLA_SPECIALIST_STAGING_AUTHORIZED": "1", "VALHALLA_SPECIALIST_GROQ_FREE_PLAN_CONFIRMED": "1",
        "VALHALLA_SPECIALIST_DAILY_REQUEST_LIMIT": "2", "VALHALLA_LOKI_GROQ_MODEL": "loki-fixture",
        "VALHALLA_OWNER_CHAT_GROQ_KEY": "fixture-shared-key", "VALHALLA_LOKI_GROQ_KEY": "fixture-shared-key",
    }.items():
        monkeypatch.setenv(key, value)
    assert client.post(f"{root}/stage-probes", json=probe, headers=owner).status_code == 503
    assert calls == []
    monkeypatch.setenv("VALHALLA_LOKI_GROQ_KEY", "fixture-independent-key")
    assert client.post(f"{root}/stage-probes", json={**probe, "private_prompt": "must never forward"}, headers=owner).status_code == 422
    response = client.post(f"{root}/stage-probes", json=probe, headers=owner)
    assert response.status_code == 201, response.text
    detail = response.json()
    assert detail["result"] == "pass"
    assert detail["prompt_tokens"] == 42
    assert detail["billing_verified"] is False
    assert client.post(f"{root}/stage-probes", json=probe, headers=owner).json() == detail
    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "https://api.groq.com/openai/v1/chat/completions"
    assert kwargs["json"]["max_completion_tokens"] == 64
    assert len(kwargs["json"]["messages"]) == 2
    failed = client.post(f"{root}/stage-probes", json={**probe, "probe_id": str(uuid4())}, headers=owner)
    assert failed.json()["result"] == "unavailable"
    assert client.post(f"{root}/stage-probes", json={**probe, "probe_id": str(uuid4())}, headers=owner).status_code == 429
    assert len(calls) == 2

    from datetime import datetime, timedelta, timezone
    from app.models.provider_pricing import ProviderPriceQuote, ProviderUsageReconciliation

    for model in (ProviderPriceQuote, ProviderUsageReconciliation):
        model.__table__.create(engine)
    today = datetime.now(timezone.utc).date()
    quote = {
        "quote_id": str(uuid4()), "provider_id": challenger_id, "source_url": "https://console.groq.com/docs/fixture-pricing",
        "observed_on": today.isoformat(), "effective_on": today.isoformat(),
        "expires_on": (today + timedelta(days=10)).isoformat(), "currency": "USD",
        "input_minor_per_million": 100, "output_minor_per_million": 200,
    }
    assert client.post(f"{root}/price-quotes", headers=owner, json={**quote, "source_url": "https://console.groq.com@foreign.invalid/"}).status_code == 422
    recorded = client.post(f"{root}/price-quotes", headers=owner, json=quote)
    assert recorded.status_code == 201, recorded.text
    assert recorded.json()["basis"] == "OWNER_RECORDED_PRICE_SOURCE"
    assert client.get(f"{root}/price-quotes", params={"provider_id": challenger_id}).json() == [recorded.json()]
    usage = f"{root}/stage-probes/{probe['probe_id']}"
    cost = client.get(f"{usage}/cost", params={"quote_id": quote["quote_id"]})
    assert cost.status_code == 200, cost.text
    assert cost.json()["estimated_microminor"] == 4400
    statement = {"quote_id": quote["quote_id"], "statement_ref": "fixture:statement-one", "reported_microminor": 4520}
    reconciled = client.post(f"{usage}/reconcile", headers=owner, json=statement)
    assert reconciled.status_code == 201, reconciled.text
    assert reconciled.json()["variance_microminor"] == 120
    assert reconciled.json()["billing_provider_verified"] is False
    assert client.post(f"{usage}/reconcile", headers=owner, json=statement).json() == reconciled.json()
    assert client.post(f"{usage}/reconcile", headers=owner, json={**statement, "reported_microminor": 5000}).status_code == 409

    routing = {"role": "LOKI", "data_class": "SYNTHETIC", "currency": "USD",
               "input_token_limit": 42, "output_token_limit": 64, "max_microminor": 18000}
    selected = client.post(f"{root}/select-staging-candidate", headers=owner, json=routing)
    assert selected.status_code == 200, selected.text
    assert selected.json()["candidate"]["provider_id"] == challenger_id
    assert selected.json()["candidate"]["estimated_max_microminor"] == 17000
    assert selected.json()["provider_call_authorized"] is False
    unaffordable = client.post(f"{root}/select-staging-candidate", headers=owner, json={**routing, "max_microminor": 16999})
    assert unaffordable.json()["candidate"] is None
    assert len(calls) == 2
