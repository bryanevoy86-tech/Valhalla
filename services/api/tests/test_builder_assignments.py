from datetime import timedelta
from hashlib import sha256
from pathlib import Path
import runpy
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.builder import BuilderEvent, BuilderTask
from app.models.builder_assignment import BuilderAssignment
from app.routers import builder, builder_assignments


def test_scoped_builder_lease_survives_restart_and_submits_review_receipt(deal_client, tmp_path, monkeypatch):
    client, engine = deal_client
    for model in (BuilderEvent, BuilderTask, BuilderAssignment):
        model.__table__.create(engine)
    monkeypatch.setattr(builder, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(settings, "BUILDER_KEY", "unit-builder-author")
    monkeypatch.setenv("VALHALLA_BUILDER_RUNNER_KEY", "unit-builder-runner")
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "unit-builder-owner")
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    author = {"X-API-Key": "unit-builder-author"}
    runner_key = {"X-Builder-Runner-Key": "unit-builder-runner"}
    owner = {"X-Owner-Mandate-Key": "unit-builder-owner"}
    task = client.post("/builder/tasks", headers=author, json={"title": "Test a bounded candidate", "scope": "API fixture"})
    assert task.status_code == 200, task.text
    task_id = task.json()["task_id"]
    path = "services/api/app/routers/safe_fixture.py"
    draft = client.post(f"/builder/draft?task_id={task_id}", headers=author,
                        json=[{"path": path, "content": "VALUE = 2\n", "mode": "add"}])
    assert draft.status_code == 200, draft.text
    assert client.post("/builder/apply", headers=author, json={"task_id": task_id, "approve": False}).status_code == 200
    assert not (tmp_path / path).exists()

    root = "/builder/assignments"
    request = {"assignment_id": str(uuid4()), "task_id": task_id, "base_commit": "a" * 40, "image_id": "sha256:" + "b" * 64}
    assert client.post(root, json=request).status_code == 401
    assigned = client.post(root, headers=owner, json=request)
    assert assigned.status_code == 201, assigned.text
    assert client.post(f"{root}/claim", headers=author).status_code == 401
    handoff = f"{root}/{request['assignment_id']}/review-handoff"
    expected = {"expected_base_commit": request["base_commit"], "expected_bundle_sha256": assigned.json()["bundle_sha256"]}
    assert client.post(handoff, headers=runner_key, json=expected).status_code == 401
    assert client.post(handoff, headers=owner, json=expected).status_code == 409
    first = client.post(f"{root}/claim", headers=runner_key).json()
    assert first["status"] == "leased"
    assert client.post(f"{root}/claim", headers=runner_key).json()["status"] == "idle"
    at = builder_assignments.now() + timedelta(minutes=16)
    monkeypatch.setattr(builder_assignments, "now", lambda: at)

    suite_root = Path(__file__).resolve().parents[3] / "scripts"
    monkeypatch.syspath_prepend(str(suite_root))
    worker = runpy.run_path(str(suite_root / "builder_assignment_worker.py"))["tick"]

    class RunnerClient:
        def post(self, path, **kwargs):
            response = client.post(path, headers=runner_key, **kwargs)
            if path.endswith("/claim"):
                assert response.json()["lease_id"] != first["lease_id"]
            return response

    def isolated_runner(review, repo, commit, image, timeout):
        assert repo == tmp_path
        assert review["sha256"] == first["bundle_sha256"]
        assert commit == request["base_commit"] and image == request["image_id"]
        return {"status": "suite_exited_zero", "exit_code": 0, "suite": "services/api/tests",
                "base_commit": commit, "image_id": image, "bundle_sha256": review["sha256"],
                "source_modified": False, "committed": False, "deployed": False, "release_authorized": False}

    outcome = worker(RunnerClient(), tmp_path, request["image_id"], runner=isolated_runner)
    assert outcome == {"status": "review_ready", "release_authorized": False}
    record = client.get(f"{root}/{request['assignment_id']}").json()
    stale = {**record["receipt"], "lease_id": first["lease_id"]}
    assert client.post(f"{root}/{request['assignment_id']}/receipt", headers=runner_key, json=stale).status_code == 409
    assert client.post(f"{root}/{request['assignment_id']}/receipt", headers=runner_key, json=record["receipt"]).json() == record
    assert client.post(f"{root}/claim", headers=runner_key).json()["status"] == "idle"
    assert not (tmp_path / path).exists()
    assert client.post(handoff, headers=owner, json={**expected, "expected_base_commit": "c" * 40}).status_code == 409
    prepared = client.post(handoff, headers=owner, json=expected)
    assert prepared.status_code == 200, prepared.text
    assert prepared.headers["cache-control"] == "no-store"
    packet = prepared.json()
    digest = packet.pop("handoff_sha256")
    assert digest == sha256(builder._canonical(packet)).hexdigest()
    assert packet["test_receipt_sha256"] == sha256(builder._canonical(record["receipt"])).hexdigest()
    assert packet["github_write_authorized"] is False and packet["release_authorized"] is False
    assert packet["review"]["bundle"]["files"][0]["content"] == "VALUE = 2\n"
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert client.post(handoff, headers=owner, json=expected).status_code == 503


def test_owner_prepares_snapshot_candidate_for_existing_runner(deal_client, tmp_path, monkeypatch):
    client, engine = deal_client
    for model in (BuilderEvent, BuilderTask, BuilderAssignment):
        model.__table__.create(engine)
    monkeypatch.setattr(builder, "_REPO_ROOT", tmp_path)
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "fixture-preparation-owner")
    monkeypatch.setenv("VALHALLA_BUILDER_RUNNER_KEY", "fixture-preparation-runner")
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    owner = {"X-Owner-Mandate-Key": "fixture-preparation-owner"}
    runner = {"X-Builder-Runner-Key": "fixture-preparation-runner"}
    path = "services/api/app/routers/scoped_fixture.py"
    target = tmp_path / path
    target.parent.mkdir(parents=True)
    original = b"VALUE = 1\n"
    target.write_bytes(original)
    endpoint = "/builder/assignments/prepare"
    request = {
        "assignment_id": str(uuid4()), "base_commit": "a" * 40, "image_id": "sha256:" + "b" * 64,
        "title": "Fix fixture value", "path": path, "source_sha256": sha256(original).hexdigest(),
        "before": "VALUE = 1", "after": "VALUE = 2",
    }
    assert client.post(endpoint, headers=runner, json=request).status_code == 401
    assert client.post(endpoint, headers=owner, json={**request, "source_sha256": "0" * 64}).status_code == 409
    assert client.post(endpoint, headers=owner, json={**request, "path": "../outside.py"}).status_code == 400
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "true")
    assert client.post(endpoint, headers=owner, json=request).status_code == 503
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    prepared = client.post(endpoint, headers=owner, json=request)
    assert prepared.status_code == 201, prepared.text
    assert client.post(endpoint, headers=owner, json=request).json() == prepared.json()
    assert client.post(endpoint, headers=owner, json={**request, "after": "VALUE = 3"}).status_code == 409
    lease = client.post("/builder/assignments/claim", headers=runner).json()
    assert lease["review"]["bundle"]["files"][0]["content"] == "VALUE = 2\n"
    assert lease["review"]["sha256"] == prepared.json()["bundle_sha256"]
    assert target.read_bytes() == original
    assert lease["review"]["deployed"] is False


    clock = [builder_assignments.now()]
    monkeypatch.setattr(builder_assignments, "now", lambda: clock[0])
    for expected in (2, 3):
        clock[0] += timedelta(minutes=16)
        replay = client.post("/builder/assignments/claim", headers=runner).json()
        assert replay["status"] == "leased" and replay["claim_count"] == expected
        assert replay["release_authorized"] is False
    clock[0] += timedelta(minutes=16)
    exhausted = client.post("/builder/assignments/claim", headers=runner).json()
    assert exhausted["status"] == "lease_exhausted" and exhausted["receipt"] is None
    assert exhausted["claim_count"] == 3 and exhausted["release_authorized"] is False
    assert client.post("/builder/assignments/claim", headers=runner).json()["status"] == "idle"


def test_owner_prepares_atomic_multifile_builder_candidate(deal_client, tmp_path, monkeypatch):
    client, engine = deal_client
    for model in (BuilderEvent, BuilderTask, BuilderAssignment):
        model.__table__.create(engine)
    monkeypatch.setattr(builder, "_REPO_ROOT", tmp_path)
    monkeypatch.setenv("VALHALLA_OWNER_MANDATE_KEY", "fixture-multifile-owner")
    monkeypatch.setenv("VALHALLA_BUILDER_RUNNER_KEY", "fixture-multifile-runner")
    monkeypatch.setenv("VALHALLA_EMERGENCY_STOP", "false")
    owner = {"X-Owner-Mandate-Key": "fixture-multifile-owner"}
    runner = {"X-Builder-Runner-Key": "fixture-multifile-runner"}
    edits = []
    for name, before, after in (("consumer", "VALUE = 1", "VALUE = 2"), ("contract", "EXPECTED = 1", "EXPECTED = 2")):
        path = f"services/api/app/routers/{name}.py"
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        source = (before + "\n").encode()
        target.write_bytes(source)
        edits.append({"path": path, "source_sha256": sha256(source).hexdigest(), "before": before, "after": after})
    request = {
        "assignment_id": str(uuid4()), "base_commit": "a" * 40, "image_id": "sha256:" + "b" * 64,
        "title": "Update consumer and contract together", "edits": edits,
    }
    endpoint = "/builder/assignments/prepare"
    assert client.post(endpoint, headers=runner, json=request).status_code == 401
    stale = {**request, "edits": [edits[0], {**edits[1], "source_sha256": "0" * 64}]}
    assert client.post(endpoint, headers=owner, json=stale).status_code == 409
    assert client.post(endpoint, headers=owner, json={**request, "edits": [edits[0], edits[0]]}).status_code == 422
    with Session(engine) as db:
        assert db.query(BuilderTask).count() == 0 and db.query(BuilderAssignment).count() == 0
        assert db.query(BuilderEvent).count() == 0
    prepared = client.post(endpoint, headers=owner, json=request)
    assert prepared.status_code == 201, prepared.text
    assert client.post(endpoint, headers=owner, json=request).json() == prepared.json()
    assert client.post(endpoint, headers=owner, json={**request, "edits": list(reversed(edits))}).status_code == 409
    lease = client.post("/builder/assignments/claim", headers=runner).json()
    assert lease["release_authorized"] is False and lease["review"]["deployed"] is False
    assert lease["review"]["sha256"] == prepared.json()["bundle_sha256"]
    for record, edit in zip(lease["review"]["bundle"]["files"], edits, strict=True):
        assert record["path"] == edit["path"]
        assert record["base_sha256"] == edit["source_sha256"]
        assert record["content"] == edit["after"] + "\n"
        assert (tmp_path / edit["path"]).read_text() == edit["before"] + "\n"
