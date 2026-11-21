from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.auth_revocations import RevokedAccessToken
from app.models.completion_registry import LearningTaskQueueItem
from app.models.go_live_state import GoLiveState
from app.models.prime_specialist_schedule import PrimeSpecialistSchedule
from app.models.saas_access import SaaSPlan, SaaSPlanModule, SaaSTenantEntitlement, Subscription
from app.routers.auth_weweb import _auth_runtime, _issue_access_token
from app.users.models import AccountSettings, UserProfile


def test_trial_is_bound_to_authenticated_subscriber_and_tenant(deal_client, monkeypatch):
    client, engine = deal_client
    key = "internal-saas-test-owner"
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", key)
    owner = {"X-Owner-Mandate-Key": key}
    for model in (SaaSPlan, SaaSPlanModule, Subscription, UserProfile, AccountSettings, RevokedAccessToken, SaaSTenantEntitlement):
        model.__table__.create(engine)

    with Session(engine) as db:
        profiles = [UserProfile(first_name="Test", last_name=label, email=f"{label}@example.invalid") for label in ("one", "two")]
        db.add_all(profiles)
        db.flush()
        for profile in profiles:
            db.add(AccountSettings(user_id=profile.user_id, account_locked=False, password_hash="unused-fixture"))
        db.commit()
        subject_id = profiles[0].user_id
        runtime = _auth_runtime()
        bearer, outsider = ({"Authorization": f"Bearer {_issue_access_token(runtime, profile)}"} for profile in profiles)

    data = {"code": "TRIAL", "name": "Internal trial", "modules": [{"module_key": "wholesale_engine"}]}
    assert client.post("/saas/plans", json=data).status_code == 401
    plan = client.post("/saas/plans", headers=owner, json=data)
    assert plan.status_code == 200, plan.text
    assert client.post("/saas/subscriptions", json={"user_id": subject_id, "plan_id": plan.json()["id"]}).status_code == 401

    trial = {
        "entitlement_id": str(uuid4()), "tenant_id": str(uuid4()), "subject_id": subject_id, "plan_id": plan.json()["id"],
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(), "modules": ["wholesale_engine"],
    }
    root = "/saas/tenant-entitlements"
    invalid_module = client.post(root, headers=owner, json={**trial, "modules": ["heimdall_prime"]})
    assert invalid_module.status_code == 422
    issued = client.post(root, headers=owner, json=trial)
    assert issued.status_code == 201, issued.text
    assert issued.json()["payment_verified"] is False
    assert client.post(root, headers=owner, json=trial).json() == issued.json()

    monkeypatch.setenv("VALHALLA_OWNER_EMAIL", "one@example.invalid")
    for model in (LearningTaskQueueItem, GoLiveState, PrimeSpecialistSchedule):
        model.__table__.create(engine)
    with Session(engine) as db:
        db.add(GoLiveState(id=1, go_live_enabled=False, kill_switch_engaged=True))
        db.commit()
    briefing = "/api/weweb/owner-briefing"
    assert client.get(briefing).status_code == 401
    assert client.get(briefing, headers=outsider).status_code == 403
    owned = client.get(briefing, headers={**bearer, "X-Prime-Control-Key": "not-used"})
    assert owned.status_code == 200, owned.text
    assert owned.headers["cache-control"] == "no-store"
    assert owned.json()["execution_authorized"] is False
    assert owned.json()["evidence"]["integrity"]["fail_safe_state"]["active"] is True

    access = f"{root}/{trial['tenant_id']}/access/wholesale_engine"
    assert client.get(access).status_code == 401
    assert client.get(access, headers=outsider).status_code == 404
    assert client.get(f"{root}/{uuid4()}/access/wholesale_engine", headers=bearer).status_code == 404
    assert client.get(access, headers=bearer).json()["has_access"]
    assert client.get(f"{root}/{trial['tenant_id']}/access/dispo_engine", headers=bearer).status_code == 404
    assert client.delete(f"{root}/{trial['entitlement_id']}", headers=owner).json()["revoked"]
    assert client.get(access, headers=bearer).status_code == 404
    assert client.post("/api/weweb/logout", headers=bearer).status_code == 200
    assert client.get(access, headers=bearer).status_code == 401
    assert client.get(briefing, headers=bearer).status_code == 401
