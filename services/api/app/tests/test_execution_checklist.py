"""
Tests for PACK CL15: Execution Checklist
"""

from fastapi.testclient import TestClient


def test_checklist_upsert_and_list(client: TestClient):
    resp = client.post(
        "/system/execution/checklist",
        json={"key": "db_migrations_applied", "title": "DB migrations applied", "description": "Alembic head applied"},
    )
    assert resp.status_code == 201, resp.text

    resp2 = client.get("/system/execution/checklist")
    assert resp2.status_code == 200
    assert resp2.json()["total"] >= 1
