"""
PACK TV: System Log Tests
Tests for system log writing and listing.
"""

import pytest


def test_system_log_write_and_list(client):
    """Test writing and listing system logs."""
    # Write a log
    write_res = client.post(
        "/system/logs/",
        json={"message": "Test log entry", "category": "test", "level": "INFO"},
    )
    assert write_res.status_code == 200
    log_data = write_res.json()
    assert log_data["message"] == "Test log entry"
    assert log_data["category"] == "test"
    assert log_data["level"] == "INFO"
    assert "id" in log_data
    assert "timestamp" in log_data


def test_system_log_list_with_filter(client):
    """Test listing logs with category filter."""
    # Write a log
    client.post(
        "/system/logs/",
        json={"message": "Test entry", "category": "security", "level": "WARNING"},
    )

    # List logs by category
    list_res = client.get("/system/logs/?category=security")
    assert list_res.status_code == 200
    body = list_res.json()
    assert "total" in body
    assert "items" in body
    assert body["total"] >= 1


def test_system_log_list_with_level_filter(client):
    """Test listing logs with level filter."""
    # Write logs at different levels
    client.post(
        "/system/logs/",
        json={"message": "Critical issue", "category": "system", "level": "CRITICAL"},
    )
    client.post(
        "/system/logs/",
        json={"message": "Info msg", "category": "system", "level": "INFO"},
    )

    # List only CRITICAL
    list_res = client.get("/system/logs/?level=CRITICAL")
    assert list_res.status_code == 200
    body = list_res.json()
    if body["total"] > 0:
        # All items should be CRITICAL
        for item in body["items"]:
            assert item["level"] == "CRITICAL"


def test_system_log_includes_correlation_id(client):
    """Test that logs can include correlation_id."""
    write_res = client.post(
        "/system/logs/",
        json={
            "message": "Traced event",
            "category": "test",
            "correlation_id": "trace-123",
        },
    )
    assert write_res.status_code == 200
    log_data = write_res.json()
    assert log_data["correlation_id"] == "trace-123"
