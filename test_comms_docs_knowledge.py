#!/usr/bin/env python
"""
Comprehensive smoke tests for PACK 1-3 (Comms, Docs, Knowledge)
Tests all endpoints, data persistence, and integration patterns
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core_gov.comms import service as comms_service
from app.core_gov.docs import service as docs_service
from app.core_gov.knowledge import service as knowledge_service


def test_suite():
    """Run all smoke tests"""
    
    tests_passed = 0
    tests_total = 0
    
    print("\n" + "="*70)
    print("COMPREHENSIVE SMOKE TESTS: PACK 1-3 (COMMS, DOCS, KNOWLEDGE)")
    print("="*70 + "\n")
    
    # PACK 1: COMMS MODULE (Templates + Outbox + Logs)
    print("PACK 1: Communication Hub (P-COMMS-1)\n" + "-"*70)
    
    # Test 1: Create template
    tests_total += 1
    try:
        template_payload = {
            "name": "Seller followup text",
            "channel": "sms",
            "body": "Hey {{name}} — just checking in about {{property}}. Want me to run numbers?",
            "tags": ["followup", "seller"]
        }
        template = comms_service.create_template(template_payload)
        assert template["id"].startswith("ct_"), f"Invalid template ID: {template['id']}"
        assert template["name"] == "Seller followup text"
        assert template["channel"] == "sms"
        print(f"  ✓ Create template: {template['id'][:16]}... (name: {template['name']})")
        tests_passed += 1
        template_id = template["id"]
    except Exception as e:
        print(f"  ✗ Create template: {e}")
    
    # Test 2: Render template
    tests_total += 1
    try:
        rendered = comms_service.render_template(template_id, {"name": "John", "property": "123 Main St"})
        assert "John" in rendered["body"]
        assert "123 Main St" in rendered["body"]
        print(f"  ✓ Render template: name='John', property='123 Main St' substituted")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Render template: {e}")
    
    # Test 3: List templates
    tests_total += 1
    try:
        templates = comms_service.list_templates()
        assert len(templates) >= 1
        assert any(t["id"] == template_id for t in templates)
        print(f"  ✓ List templates: Found {len(templates)} template(s)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ List templates: {e}")
    
    # Test 4: Create outbox item (draft)
    tests_total += 1
    try:
        outbox_payload = {
            "channel": "sms",
            "to": "+1555123456",
            "body": "Hey John — just checking in about 123 Main St. Want me to run numbers?",
            "status": "draft",
            "priority": "B",
            "deal_id": "dl_test123"
        }
        outbox = comms_service.create_outbox(outbox_payload)
        assert outbox["id"].startswith("ob_"), f"Invalid outbox ID: {outbox['id']}"
        assert outbox["status"] == "draft"
        print(f"  ✓ Create outbox (draft): {outbox['id'][:16]}... (to: {outbox['to']})")
        tests_passed += 1
        outbox_id = outbox["id"]
    except Exception as e:
        print(f"  ✗ Create outbox: {e}")
    
    # Test 5: Set outbox status (queued)
    tests_total += 1
    try:
        queued = comms_service.set_status(outbox_id, "queued")
        assert queued["status"] == "queued"
        print(f"  ✓ Set status to queued: {outbox_id[:16]}...")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Set status to queued: {e}")
    
    # Test 6: Set outbox status (sent)
    tests_total += 1
    try:
        sent = comms_service.set_status(outbox_id, "sent")
        assert sent["status"] == "sent"
        assert sent["sent_at"] != ""
        print(f"  ✓ Set status to sent: {outbox_id[:16]}... (sent_at populated)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Set status to sent: {e}")
    
    # Test 7: List outbox (filter by status)
    tests_total += 1
    try:
        sent_items = comms_service.list_outbox(status="sent")
        assert len(sent_items) >= 1
        assert any(item["id"] == outbox_id for item in sent_items)
        print(f"  ✓ List outbox (sent): Found {len(sent_items)} item(s)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ List outbox (sent): {e}")
    
    # Test 8: List logs
    tests_total += 1
    try:
        logs = comms_service.list_logs()
        assert len(logs) >= 3  # template_created + outbox_created + status changes
        print(f"  ✓ List logs: Found {len(logs)} log entries")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ List logs: {e}")
    
    # PACK 2: DOCS MODULE (Document Vault)
    print("\nPACK 2: Document Vault (P-DOCS-2)\n" + "-"*70)
    
    # Test 9: Create document (receipt)
    tests_total += 1
    try:
        doc_payload = {
            "doc_type": "receipt",
            "title": "Walmart groceries receipt",
            "file_ref": "photos/receipt_2026-01-02.jpg",
            "amount": 120.50,
            "date": "2026-01-02",
            "merchant": "Walmart",
            "tags": ["groceries", "household"]
        }
        doc = docs_service.create_doc(doc_payload)
        assert doc["id"].startswith("dc_"), f"Invalid doc ID: {doc['id']}"
        assert doc["title"] == "Walmart groceries receipt"
        assert doc["amount"] == 120.50
        print(f"  ✓ Create document: {doc['id'][:16]}... (amount: ${doc['amount']})")
        tests_passed += 1
        doc_id = doc["id"]
    except Exception as e:
        print(f"  ✗ Create document: {e}")
    
    # Test 10: Create document (invoice)
    tests_total += 1
    try:
        invoice_payload = {
            "doc_type": "invoice",
            "title": "Q1 office supplies invoice",
            "file_ref": "invoices/office_2026_q1.pdf",
            "amount": 450.00,
            "date": "2026-01-10",
            "merchant": "Staples",
            "tags": ["office", "supplies"]
        }
        invoice = docs_service.create_doc(invoice_payload)
        assert invoice["id"].startswith("dc_")
        print(f"  ✓ Create invoice: {invoice['id'][:16]}... (amount: ${invoice['amount']})")
        tests_passed += 1
        invoice_id = invoice["id"]
    except Exception as e:
        print(f"  ✗ Create invoice: {e}")
    
    # Test 11: List documents (by type)
    tests_total += 1
    try:
        receipts = docs_service.list_docs(doc_type="receipt")
        assert len(receipts) >= 1
        assert any(d["id"] == doc_id for d in receipts)
        print(f"  ✓ List documents (receipts): Found {len(receipts)} receipt(s)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ List documents: {e}")
    
    # Test 12: Get document
    tests_total += 1
    try:
        doc = docs_service.get_doc(doc_id)
        assert doc is not None
        assert doc["id"] == doc_id
        print(f"  ✓ Get document: {doc_id[:16]}... (title: {doc['title']})")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Get document: {e}")
    
    # Test 13: Patch document (update)
    tests_total += 1
    try:
        patch = {"merchant": "Walmart Supercenter", "notes": "Grocery run + household items"}
        updated = docs_service.patch_doc(doc_id, patch)
        assert updated["merchant"] == "Walmart Supercenter"
        assert updated["notes"] == "Grocery run + household items"
        print(f"  ✓ Patch document: merchant and notes updated")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Patch document: {e}")
    
    # Test 14: List all documents
    tests_total += 1
    try:
        all_docs = docs_service.list_docs()
        assert len(all_docs) >= 2
        print(f"  ✓ List all documents: Found {len(all_docs)} document(s)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ List all documents: {e}")
    
    # PACK 3: KNOWLEDGE MODULE (Ingestion + Retrieval)
    print("\nPACK 3: Knowledge Vault (P-KNOW-2)\n" + "-"*70)
    
    # Test 15: Ingest text
    tests_total += 1
    try:
        ingest_payload = {
            "source_title": "Valhalla budgeting rules",
            "source_type": "note",
            "text": "Essentials first. Autopay must be verified. Discretionary blocked if obligations not covered. Always keep capital buffer above minimum.",
            "tags": ["budget", "rules", "essential"]
        }
        ingested = knowledge_service.ingest_text(ingest_payload)
        assert "source" in ingested
        assert ingested["source"]["id"].startswith("ks_")
        assert ingested["chunks_added"] > 0
        print(f"  ✓ Ingest text: {ingested['source']['id'][:16]}... ({ingested['chunks_added']} chunks)")
        tests_passed += 1
        source_id = ingested["source"]["id"]
    except Exception as e:
        print(f"  ✗ Ingest text: {e}")
    
    # Test 16: Ingest another text
    tests_total += 1
    try:
        ingest_payload2 = {
            "source_title": "Property investment criteria",
            "source_type": "doc",
            "source_ref": "criteria_2026_v2",
            "text": "Target properties must have positive cashflow. Minimum cap rate 8%. Location critical for tenant quality. Avoid high-vacancy areas. Focus on workforce housing or student housing.",
            "tags": ["investing", "criteria"]
        }
        ingested2 = knowledge_service.ingest_text(ingest_payload2)
        assert ingested2["chunks_added"] > 0
        print(f"  ✓ Ingest second text: {ingested2['source']['id'][:16]}... ({ingested2['chunks_added']} chunks)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Ingest second text: {e}")
    
    # Test 17: Retrieve (simple query)
    tests_total += 1
    try:
        retrieve_payload = {"query": "obligations covered", "k": 5}
        result = knowledge_service.retrieve(retrieve_payload["query"], k=retrieve_payload["k"])
        assert len(result) > 0
        assert result[0]["score"] > 0
        print(f"  ✓ Retrieve query 'obligations covered': {len(result)} hit(s), top score: {result[0]['score']}")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Retrieve simple query: {e}")
    
    # Test 18: Retrieve (complex query)
    tests_total += 1
    try:
        result2 = knowledge_service.retrieve("discretionary blocked", k=3)
        assert len(result2) > 0
        print(f"  ✓ Retrieve query 'discretionary blocked': {len(result2)} hit(s)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Retrieve complex query: {e}")
    
    # Test 19: Retrieve with tag filter
    tests_total += 1
    try:
        result3 = knowledge_service.retrieve("cashflow cap rate", k=5, tag="investing")
        # Should return at least one hit filtered by tag
        assert len(result3) > 0, "Tag filter should return at least one hit with matching content"
        print(f"  ✓ Retrieve with tag filter 'investing': {len(result3)} hit(s)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Retrieve with tag filter: {e}")
    
    # Test 20: List sources
    tests_total += 1
    try:
        sources = knowledge_service.list_sources()
        assert len(sources) >= 2
        assert any(s["id"] == source_id for s in sources)
        print(f"  ✓ List sources: Found {len(sources)} source(s)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ List sources: {e}")
    
    # DATA PERSISTENCE
    print("\nDATA PERSISTENCE\n" + "-"*70)
    
    # Test 21: Check templates.json
    tests_total += 1
    try:
        templates_path = os.path.join("backend", "data", "comms", "templates.json")
        assert os.path.exists(templates_path)
        with open(templates_path, "r") as f:
            data = json.load(f)
        assert len(data.get("items", [])) >= 1
        file_size = os.path.getsize(templates_path)
        print(f"  ✓ templates.json persisted ({file_size} bytes, {len(data['items'])} items)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ templates.json: {e}")
    
    # Test 22: Check outbox.json
    tests_total += 1
    try:
        outbox_path = os.path.join("backend", "data", "comms", "outbox.json")
        assert os.path.exists(outbox_path)
        with open(outbox_path, "r") as f:
            data = json.load(f)
        assert len(data.get("items", [])) >= 1
        file_size = os.path.getsize(outbox_path)
        print(f"  ✓ outbox.json persisted ({file_size} bytes, {len(data['items'])} items)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ outbox.json: {e}")
    
    # Test 23: Check docs.json
    tests_total += 1
    try:
        docs_path = os.path.join("backend", "data", "docs", "docs.json")
        assert os.path.exists(docs_path)
        with open(docs_path, "r") as f:
            data = json.load(f)
        assert len(data.get("items", [])) >= 2
        file_size = os.path.getsize(docs_path)
        print(f"  ✓ docs.json persisted ({file_size} bytes, {len(data['items'])} items)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ docs.json: {e}")
    
    # Test 24: Check knowledge files
    tests_total += 1
    try:
        sources_path = os.path.join("backend", "data", "knowledge", "sources.json")
        chunks_path = os.path.join("backend", "data", "knowledge", "chunks.json")
        index_path = os.path.join("backend", "data", "knowledge", "index.json")
        assert os.path.exists(sources_path)
        assert os.path.exists(chunks_path)
        assert os.path.exists(index_path)
        with open(sources_path, "r") as f:
            sources_data = json.load(f)
        with open(chunks_path, "r") as f:
            chunks_data = json.load(f)
        with open(index_path, "r") as f:
            index_data = json.load(f)
        print(f"  ✓ Knowledge files persisted:")
        print(f"      - sources.json ({len(sources_data['items'])} sources)")
        print(f"      - chunks.json ({len(chunks_data['items'])} chunks)")
        print(f"      - index.json ({len(index_data['index'])} tokens)")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Knowledge files: {e}")
    
    # SUMMARY
    print("\n" + "="*70)
    print(f"RESULTS: {tests_passed}/{tests_total} PASSED ({100*tests_passed//tests_total}%)")
    print("="*70 + "\n")
    
    if tests_passed == tests_total:
        print("✅ ALL TESTS PASSED — PACK 1-3 READY FOR DEPLOYMENT\n")
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} TEST(S) FAILED\n")
        return 1


if __name__ == "__main__":
    sys.exit(test_suite())
