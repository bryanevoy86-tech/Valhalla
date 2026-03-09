#!/usr/bin/env python3
"""
Comprehensive unit tests for P-DOCS-1, P-KNOW-1, P-COMMS-1
Tests direct module imports without requiring FastAPI server
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ""))

# ============================================================================
# P-DOCS-1 TESTS
# ============================================================================

def test_docs_create():
    """Test P-DOCS-1: Create document"""
    from backend.app.core_gov.docs import service as docs_service
    
    payload = {
        "title": "Lease Agreement",
        "doc_type": "contract",
        "visibility": "internal",
        "file_path": "/docs/lease_2024.pdf",
        "mime": "application/pdf",
        "tags": ["lease", "property"],
        "links": {"property": "pi_abc123"},
        "notes": "Main lease document"
    }
    
    doc = docs_service.create_doc(payload)
    assert doc["id"].startswith("dc_")
    assert doc["title"] == "Lease Agreement"
    assert doc["doc_type"] == "contract"
    assert "lease" in doc["tags"]
    print(f"  ✓ Created doc: {doc['id']}")
    return doc["id"]


def test_docs_list(doc_id):
    """Test P-DOCS-1: List documents"""
    from backend.app.core_gov.docs import service as docs_service
    
    docs = docs_service.list_docs()
    assert len(docs) >= 1
    assert any(d["id"] == doc_id for d in docs)
    print(f"  ✓ Listed {len(docs)} document(s)")
    
    # Filter by tag
    docs_by_tag = docs_service.list_docs(tag="lease")
    assert len(docs_by_tag) >= 1
    print(f"  ✓ Filtered by tag: {len(docs_by_tag)} document(s)")


def test_docs_get(doc_id):
    """Test P-DOCS-1: Get single document"""
    from backend.app.core_gov.docs import service as docs_service
    
    doc = docs_service.get_doc(doc_id)
    assert doc is not None
    assert doc["id"] == doc_id
    print(f"  ✓ Retrieved document: {doc['title']}")


def test_docs_patch(doc_id):
    """Test P-DOCS-1: Patch document"""
    from backend.app.core_gov.docs import service as docs_service
    
    patch = {
        "title": "Lease Agreement (Updated)",
        "visibility": "shareable",
        "tags": ["lease", "property", "executed"]
    }
    
    doc = docs_service.patch_doc(doc_id, patch)
    assert doc["title"] == "Lease Agreement (Updated)"
    assert doc["visibility"] == "shareable"
    assert "executed" in doc["tags"]
    print(f"  ✓ Patched document: {doc['title']}")


def test_docs_bundle(doc_id):
    """Test P-DOCS-1: Create bundle"""
    from backend.app.core_gov.docs import service as docs_service
    
    bundle = docs_service.create_bundle(
        name="Property Bundle",
        doc_ids=[doc_id],
        include_links=True,
        include_notes=True,
        meta={"purpose": "sharing"}
    )
    
    assert bundle["id"].startswith("bd_")
    assert bundle["name"] == "Property Bundle"
    assert bundle["manifest"]["doc_count"] == 1
    assert len(bundle["manifest"]["docs"]) == 1
    print(f"  ✓ Created bundle: {bundle['id']} with {bundle['manifest']['doc_count']} doc(s)")


# ============================================================================
# P-KNOW-1 TESTS
# ============================================================================

def test_knowledge_ingest_create():
    """Test P-KNOW-1: Create inbox item"""
    from backend.app.core_gov.knowledge_ingest import service as ki_service
    
    payload = {
        "title": "Funding Research",
        "source_type": "note",
        "raw_text": "Looking into grants and loans. Small business administration (SBA) programs available. Also checking business credit options.",
        "tags": ["funding", "research"],
        "meta": {"priority": "high"}
    }
    
    item = ki_service.create_inbox(payload)
    assert item["id"].startswith("ki_")
    assert item["title"] == "Funding Research"
    assert item["stage"] == "inbox"
    print(f"  ✓ Created inbox item: {item['id']}")
    return item["id"]


def test_knowledge_ingest_process(item_id):
    """Test P-KNOW-1: Process item (clean, chunk, index)"""
    from backend.app.core_gov.knowledge_ingest import service as ki_service
    
    result = ki_service.process(
        item_id=item_id,
        action="all",
        max_chunk_chars=900,
        overlap_chars=120
    )
    
    assert result["ok"] is True
    assert result["item_id"] == item_id
    print(f"  ✓ Processed item: {result['action']}")
    
    # Verify item stage updated
    item = ki_service.get_inbox(item_id)
    assert item["stage"] == "indexed"
    print(f"  ✓ Item progressed to stage: {item['stage']}")


def test_knowledge_ingest_search(item_id):
    """Test P-KNOW-1: Search indexed content"""
    from backend.app.core_gov.knowledge_ingest import service as ki_service
    
    result = ki_service.search(
        query="grants loans funding",
        top_k=5,
        item_id=item_id
    )
    
    assert "query" in result
    assert "hits" in result
    assert len(result["hits"]) > 0
    print(f"  ✓ Search found {len(result['hits'])} hit(s)")
    
    if result["hits"]:
        hit = result["hits"][0]
        assert "score" in hit
        assert "snippet" in hit
        print(f"  ✓ Top hit score: {hit['score']:.2f}")


def test_knowledge_ingest_list():
    """Test P-KNOW-1: List inbox items"""
    from backend.app.core_gov.knowledge_ingest import service as ki_service
    
    items = ki_service.list_inbox()
    assert len(items) >= 1
    print(f"  ✓ Listed {len(items)} inbox item(s)")
    
    # Filter by stage
    indexed = ki_service.list_inbox(stage="indexed")
    assert len(indexed) >= 1
    print(f"  ✓ Found {len(indexed)} indexed item(s)")


# ============================================================================
# P-COMMS-1 TESTS
# ============================================================================

def test_comms_create():
    """Test P-COMMS-1: Create message"""
    from backend.app.core_gov.comms import service as comms_service
    
    payload = {
        "title": "Buyer Introduction",
        "channel": "email",
        "status": "draft",
        "tone": "warm",
        "to": "buyer@example.com",
        "subject": "Off-Market Opportunity",
        "body": "Hi there, I have an interesting deal for you...",
        "deal_id": "dl_123",
        "tags": ["buyer", "deal"],
    }
    
    msg = comms_service.create_message(payload)
    assert msg["id"].startswith("cm_")
    assert msg["title"] == "Buyer Introduction"
    assert msg["status"] == "draft"
    assert msg["channel"] == "email"
    print(f"  ✓ Created message: {msg['id']}")
    return msg["id"]


def test_comms_list(msg_id):
    """Test P-COMMS-1: List messages"""
    from backend.app.core_gov.comms import service as comms_service
    
    msgs = comms_service.list_messages()
    assert len(msgs) >= 1
    assert any(m["id"] == msg_id for m in msgs)
    print(f"  ✓ Listed {len(msgs)} message(s)")
    
    # Filter by status
    drafts = comms_service.list_messages(status="draft")
    assert len(drafts) >= 1
    print(f"  ✓ Found {len(drafts)} draft message(s)")


def test_comms_get(msg_id):
    """Test P-COMMS-1: Get single message"""
    from backend.app.core_gov.comms import service as comms_service
    
    msg = comms_service.get_message(msg_id)
    assert msg is not None
    assert msg["id"] == msg_id
    print(f"  ✓ Retrieved message: {msg['title']}")


def test_comms_patch(msg_id):
    """Test P-COMMS-1: Patch message"""
    from backend.app.core_gov.comms import service as comms_service
    
    patch = {
        "status": "queued",
        "tone": "firm",
        "body": "Hi there, I have an interesting deal for you. Let me know if interested."
    }
    
    msg = comms_service.patch_message(msg_id, patch)
    assert msg["status"] == "queued"
    assert msg["tone"] == "firm"
    print(f"  ✓ Patched message status: {msg['status']}")


def test_comms_mark_sent(msg_id):
    """Test P-COMMS-1: Mark message as sent"""
    from backend.app.core_gov.comms import service as comms_service
    
    msg = comms_service.mark_sent(
        msg_id=msg_id,
        sent_at="",
        meta={"delivery_status": "delivered"}
    )
    
    assert msg["status"] == "sent"
    assert msg["sent_at"] != ""
    print(f"  ✓ Marked message as sent at: {msg['sent_at']}")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("\n" + "="*70)
    print("PACK 1-3 UNIT TESTS: P-DOCS-1, P-KNOW-1, P-COMMS-1")
    print("="*70 + "\n")
    
    # P-DOCS-1 Tests
    print("[SECTION] P-DOCS-1 (Document Vault)")
    print("-" * 70)
    try:
        doc_id = test_docs_create()
        test_docs_list(doc_id)
        test_docs_get(doc_id)
        test_docs_patch(doc_id)
        test_docs_bundle(doc_id)
        print("[SECTION PASS] P-DOCS-1 - All tests passed\n")
        docs_pass = True
    except Exception as e:
        print(f"[SECTION FAIL] P-DOCS-1 - {str(e)}\n")
        docs_pass = False
    
    # P-KNOW-1 Tests
    print("[SECTION] P-KNOW-1 (Knowledge Ingestion)")
    print("-" * 70)
    try:
        item_id = test_knowledge_ingest_create()
        test_knowledge_ingest_process(item_id)
        test_knowledge_ingest_search(item_id)
        test_knowledge_ingest_list()
        print("[SECTION PASS] P-KNOW-1 - All tests passed\n")
        know_pass = True
    except Exception as e:
        print(f"[SECTION FAIL] P-KNOW-1 - {str(e)}\n")
        know_pass = False
    
    # P-COMMS-1 Tests
    print("[SECTION] P-COMMS-1 (Communications Hub)")
    print("-" * 70)
    try:
        msg_id = test_comms_create()
        test_comms_list(msg_id)
        test_comms_get(msg_id)
        test_comms_patch(msg_id)
        test_comms_mark_sent(msg_id)
        print("[SECTION PASS] P-COMMS-1 - All tests passed\n")
        comms_pass = True
    except Exception as e:
        print(f"[SECTION FAIL] P-COMMS-1 - {str(e)}\n")
        comms_pass = False
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"P-DOCS-1 (Document Vault):       {'PASS' if docs_pass else 'FAIL'}")
    print(f"P-KNOW-1 (Knowledge Ingestion):  {'PASS' if know_pass else 'FAIL'}")
    print(f"P-COMMS-1 (Communications):      {'PASS' if comms_pass else 'FAIL'}")
    print()
    
    if docs_pass and know_pass and comms_pass:
        print("Overall: ALL SYSTEMS OPERATIONAL ✓")
        print("="*70 + "\n")
        return 0
    else:
        print("Overall: SOME SYSTEMS FAILED ✗")
        print("="*70 + "\n")
        return 1


if __name__ == "__main__":
    exit(main())
