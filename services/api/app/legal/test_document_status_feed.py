"""
Tests for document_status_feed.py
"""

from app.legal.document_status_feed import (
    get_document_status_summary,
    get_document_status_feed,
    get_package_history,
    get_audit_event_feed,
)


def test_status_summary_returns_expected_keys():
    """Verify status summary has all required fields."""
    result = get_document_status_summary()
    
    assert isinstance(result, dict)
    assert "total_documents" in result
    assert "queued_pending_approval" in result
    assert "approved_pending_send" in result
    assert "sent" in result
    assert "unknown" in result
    
    # Verify all values are ints
    assert all(isinstance(v, int) for v in result.values())


def test_status_feed_returns_structure():
    """Verify status feed returns proper structure."""
    result = get_document_status_feed(limit=10)
    
    assert isinstance(result, dict)
    assert "summary" in result
    assert "items" in result
    
    # Verify summary structure
    summary = result["summary"]
    assert "total_documents" in summary
    
    # Verify items is a list
    assert isinstance(result["items"], list)
    
    # Verify each item has required fields
    for item in result["items"]:
        assert "approval_id" in item
        assert "template_key" in item
        assert "status" in item
        assert "approved" in item
        assert "sent" in item


def test_package_history_returns_structure():
    """Verify package history returns proper structure."""
    result = get_package_history(limit=10)
    
    assert isinstance(result, dict)
    assert "package_count" in result
    assert "packages" in result
    assert isinstance(result["packages"], list)
    
    # Verify package structure
    for package in result["packages"]:
        assert "package_id" in package
        assert "document_count" in package
        assert "sent_count" in package
        assert "approved_count" in package
        assert "pending_count" in package
        assert "documents" in package


def test_audit_feed_returns_structure():
    """Verify audit feed returns proper structure."""
    result = get_audit_event_feed(limit=20)
    
    assert isinstance(result, dict)
    assert "total_events" in result
    assert "events" in result
    assert isinstance(result["events"], list)
    
    # Verify event structure
    for event in result["events"]:
        assert "timestamp" in event
        assert "event_type" in event
