"""
Tests for PACK CL17: Activation Gates
"""

from fastapi.testclient import TestClient


def test_activation_gate_upsert_and_lock(client: TestClient):
    r = client.post(
        "/system/activation/gates",
        json={
            "gate_key": "wholesale_engine",
            "title": "Wholesale Engine Activation",
            "description": "Must be green before wholesale activation",
            "requirements": {"requires": ["db_migrations_applied", "health_ok"]},
            "is_enabled": False,
        },
    )
    assert r.status_code == 201, r.text

    lock = client.post("/system/activation/gates/wholesale_engine/lock", json={"is_locked": True, "lock_reason": "manual lock"})
    assert lock.status_code == 200, lock.text

    # Try to update while locked (should not change is_enabled)
    r2 = client.post(
        "/system/activation/gates",
        json={
            "gate_key": "wholesale_engine",
            "title": "Wholesale Engine Activation",
            "description": "attempt change",
            "requirements": {"requires": []},
            "is_enabled": True,
        },
    )
    assert r2.status_code == 201, r2.text
    assert r2.json()["is_enabled"] is False
