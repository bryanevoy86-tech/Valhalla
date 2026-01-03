"""
Unit tests for P-AUTOMATE-2, P-SEC-1, P-DOCS-2 (Bridge).
Direct module imports, no server required.
"""

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone

import pytest

# P-AUTOMATE-2 tests
def test_automation_schemas():
    """Verify RunRequest, RunRecord, RunListResponse schemas."""
    from backend.app.core_gov.automation.schemas import RunRequest, RunRecord, RunListResponse
    
    req = RunRequest(run_type="nightly", month="2025-01")
    assert req.run_type == "nightly"
    assert req.month == "2025-01"
    
    rec = RunRecord(
        id="ar_test123",
        run_type="manual",
        created_at=datetime.now(timezone.utc),
        warnings=["test warning"],
        results={"test": "data"}
    )
    assert rec.id == "ar_test123"
    assert len(rec.warnings) == 1
    
    resp = RunListResponse(items=[rec])
    assert len(resp.items) == 1


def test_automation_store_ensure():
    """Test run store initialization."""
    from backend.app.core_gov.automation import store
    
    # Should not raise
    store._ensure()
    assert os.path.exists(store.RUNS_PATH)


def test_automation_store_list_save():
    """Test run list/save operations."""
    from backend.app.core_gov.automation import store
    
    store._ensure()
    initial = store.list_runs()
    assert isinstance(initial, list)
    
    test_items = [
        {"id": "ar_test1", "run_type": "manual", "created_at": "2025-01-01T00:00:00Z"},
        {"id": "ar_test2", "run_type": "nightly", "created_at": "2025-01-02T00:00:00Z"}
    ]
    store.save_runs(test_items)
    
    loaded = store.list_runs()
    assert len(loaded) == 2
    assert loaded[0]["id"] == "ar_test1"


def test_automation_service_run_house_ops():
    """Test nightly run generation."""
    from backend.app.core_gov.automation import service
    
    result = service.run_house_ops(run_type="nightly", month="2025-01", meta={"source": "test"})
    
    assert result["id"].startswith("ar_")
    assert result["run_type"] == "nightly"
    assert "created_at" in result
    assert "results" in result
    assert "bill_calendar_next_30" in result["results"]
    assert "obligations_status" in result["results"]
    assert "followups_due" in result["results"]
    assert "budget_month_snapshot" in result["results"]
    assert "reorder_candidates" in result["results"]
    assert result["meta"]["source"] == "test"


def test_automation_service_list_runs():
    """Test listing recent runs."""
    from backend.app.core_gov.automation import service
    
    # Generate a run first
    service.run_house_ops(run_type="manual")
    
    runs = service.list_runs(limit=10)
    assert isinstance(runs, list)
    if runs:
        assert "id" in runs[0]
        assert runs[0]["id"].startswith("ar_")


def test_automation_service_get_run():
    """Test retrieving a specific run."""
    from backend.app.core_gov.automation import service
    
    result = service.run_house_ops(run_type="manual")
    run_id = result["id"]
    
    retrieved = service.get_run(run_id)
    assert retrieved is not None
    assert retrieved["id"] == run_id
    
    missing = service.get_run("ar_nonexistent")
    assert missing is None


def test_automation_safe_call_graceful_degradation():
    """Test that _safe_call handles missing modules gracefully."""
    from backend.app.core_gov.automation import service
    
    warnings = []
    
    # Call safe_call with a missing module
    result = service._safe_call(
        lambda: __import__("nonexistent_module_xyz").foo(),
        warnings,
        "test_module"
    )
    
    assert result is None
    assert len(warnings) == 1
    assert "test_module" in warnings[0]


# P-SEC-1 tests
def test_security_schemas():
    """Verify security request/response schemas."""
    from backend.app.core_gov.security.schemas import (
        RedactTextRequest, RedactTextResponse,
        SanitizeManifestRequest, SanitizeManifestResponse
    )
    
    req = RedactTextRequest(text="email@example.com", level="shareable")
    assert req.level == "shareable"
    
    resp = RedactTextResponse(redacted="[REDACTED_EMAIL]")
    assert "[REDACTED" in resp.redacted


def test_security_redact_email():
    """Test email redaction."""
    from backend.app.core_gov.security import service
    
    result = service.redact_text("Contact me at john@example.com", level="shareable")
    assert "[REDACTED_EMAIL]" in result["redacted"]
    assert "john@example.com" not in result["redacted"]


def test_security_redact_phone():
    """Test phone redaction."""
    from backend.app.core_gov.security import service
    
    result = service.redact_text("Call me at 555-123-4567 or 1-800-555-1234", level="shareable")
    # Should redact properly formatted phone numbers with separators
    assert "[REDACTED_PHONE]" in result["redacted"]


def test_security_redact_long_digits():
    """Test long digit string redaction."""
    from backend.app.core_gov.security import service
    
    result = service.redact_text("Account Number: 1234567890123", level="shareable")
    # Should redact 13+ digit sequences
    assert "[REDACTED_NUMBER]" in result["redacted"]


def test_security_redact_address_strict():
    """Test address redaction in strict mode."""
    from backend.app.core_gov.security import service
    
    result = service.redact_text("123 Main Street, Apt 5", level="strict")
    # Strict mode should mask addresses
    assert "strict" in result["meta"]["level"]


def test_security_sanitize_manifest():
    """Test manifest sanitization."""
    from backend.app.core_gov.security import service
    
    manifest = {
        "name": "test_bundle",
        "docs": [
            {
                "id": "doc_123",
                "title": "Test Doc",
                "file_path": "/sensitive/path/file.pdf",
                "blob_ref": "blob:xyz",
                "sha256": "abcd1234",
                "notes": "email@example.com"
            }
        ]
    }
    
    result = service.sanitize_manifest(manifest, level="shareable")
    
    assert result["sanitized"] is True
    assert result["sanitized_level"] == "shareable"
    assert len(result["docs"]) == 1
    assert "file_path" not in result["docs"][0]
    assert "blob_ref" not in result["docs"][0]
    assert "sha256" not in result["docs"][0]
    assert "[REDACTED_EMAIL]" in result["docs"][0]["notes"]


# P-DOCS-2 Bridge tests
def test_bridge_attach_doc_as_source():
    """Test converting doc to knowledge source."""
    from backend.app.core_gov.docs import bridge
    
    doc = {
        "id": "doc_123",
        "title": "Investment Analysis",
        "body": "This is a detailed analysis of the property investment opportunity..."
    }
    
    source = bridge.attach_doc_as_source(doc, title="Custom Title", snippet="Custom snippet")
    
    assert source["source_type"] == "doc"
    assert source["doc_id"] == "doc_123"
    assert source["title"] == "Custom Title"
    assert source["snippet"] == "Custom snippet"
    assert "attached_at" in source


def test_bridge_attach_doc_fallback_title():
    """Test doc-to-source with fallback title."""
    from backend.app.core_gov.docs import bridge
    
    doc = {
        "id": "doc_456",
        "title": "Deal Summary",
        "body": "Deal details"
    }
    
    source = bridge.attach_doc_as_source(doc)  # No title override
    
    assert source["title"] == "Deal Summary"  # Uses doc title


def test_bridge_sanitize_manifest_with_fallback():
    """Test manifest sanitization with fallback."""
    from backend.app.core_gov.docs import bridge
    
    manifest = {
        "name": "shareable_bundle",
        "docs": [
            {
                "id": "doc_789",
                "title": "Summary",
                "file_path": "/private/path",
                "blob_ref": "blob:secret",
                "sha256": "hash"
            }
        ]
    }
    
    result = bridge.sanitize_manifest(manifest, level="shareable")
    
    assert result["sanitized"] is True
    assert "file_path" not in result["docs"][0]
    assert "blob_ref" not in result["docs"][0]


# Integration tests
def test_automation_full_workflow():
    """Test complete automation workflow: request → run → list → retrieve."""
    from backend.app.core_gov.automation import service
    from backend.app.core_gov.automation.schemas import RunRequest
    
    # Create request
    req = RunRequest(run_type="nightly", month="2025-01", meta={"test": True})
    
    # Run
    result = service.run_house_ops(
        run_type=req.run_type,
        month=req.month,
        meta=req.meta
    )
    
    # List
    runs = service.list_runs(limit=1)
    assert len(runs) > 0
    
    # Retrieve
    retrieved = service.get_run(result["id"])
    assert retrieved is not None
    assert retrieved["id"] == result["id"]


def test_security_full_workflow():
    """Test complete security workflow: redact and sanitize."""
    from backend.app.core_gov.security import service
    from backend.app.core_gov.security.schemas import RedactTextRequest, SanitizeManifestRequest
    
    # Redact
    text_req = RedactTextRequest(
        text="Contact john@example.com or 555-1234567",
        level="shareable"
    )
    redacted = service.redact_text(text_req.text, level=text_req.level)
    assert "[REDACTED" in redacted["redacted"]
    
    # Sanitize manifest
    manifest = {
        "docs": [{"id": "d1", "file_path": "/x", "blob_ref": "b1", "sha256": "h1"}]
    }
    manifest_req = SanitizeManifestRequest(manifest=manifest, level="shareable")
    sanitized = service.sanitize_manifest(manifest_req.manifest, level=manifest_req.level)
    assert "file_path" not in sanitized["docs"][0]


def test_automation_run_persistence():
    """Test that runs are persisted to JSON."""
    from backend.app.core_gov.automation import service, store
    
    store._ensure()
    initial_count = len(store.list_runs())
    
    # Generate a run
    result = service.run_house_ops(run_type="test_persist")
    
    # Reload from disk
    reloaded = store.list_runs()
    assert len(reloaded) > initial_count
    
    # Find the generated run
    found = any(r["id"] == result["id"] for r in reloaded)
    assert found


def test_automation_run_pruning():
    """Test that old runs are pruned (keeping last 200)."""
    from backend.app.core_gov.automation import service, store
    
    store._ensure()
    
    # Create 250 dummy runs
    items = []
    for i in range(250):
        items.append({
            "id": f"ar_prune_test_{i:03d}",
            "run_type": "test",
            "created_at": f"2025-01-{(i % 28) + 1:02d}T{i % 24:02d}:00:00Z"
        })
    store.save_runs(items)
    
    # Trigger pruning by running house_ops
    service.run_house_ops(run_type="test_prune_trigger")
    
    # Check final count (should be 200 + 1 new = 201)
    final = store.list_runs()
    assert len(final) <= 201


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
