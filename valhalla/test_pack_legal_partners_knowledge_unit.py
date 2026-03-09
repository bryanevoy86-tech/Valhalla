"""
Unit tests for P-LEGAL-1, P-PARTNER-1, P-KNOW-3 (direct module testing)

Tests core functionality without needing FastAPI server:
- Legal filter: seed defaults, run jurisdiction check
- Partners: create partner, create note, get dashboard
- Knowledge: attach sources, format citations
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.core_gov.legal_filter import service as legal_service
from app.core_gov.partners import service as partners_service
from app.core_gov.knowledge import service as knowledge_service


def test_legal_seed_defaults():
    """Seed default jurisdiction profiles"""
    print("\n[LEGAL] Seeding default profiles...")
    result = legal_service.seed_defaults_if_empty()
    print(f"  ✓ Seeded: {result.get('seeded')}, Count: {result.get('count')}")
    assert result.get("count", 0) >= 2, "Expected at least 2 profiles"


def test_legal_get_profiles():
    """List profiles"""
    print("\n[LEGAL] Listing profiles...")
    items = legal_service.list_profiles()
    print(f"  ✓ Found {len(items)} profile(s)")
    for item in items[:3]:
        print(f"    • {item['key']}: {item['name']}")
    assert len(items) > 0, "Expected at least 1 profile"


def test_legal_check_mb():
    """Run check for CA:MB jurisdiction"""
    print("\n[LEGAL] Running check for CA:MB (wholesale strategy)...")
    payload = {
        "strategy": "wholesale",
        "seller": {"id_verified": False},
        "buyer": {"entity_type": ""}
    }
    result = legal_service.run_check(
        jurisdiction_key="CA:MB",
        subject="deal",
        payload=payload,
        mode="execute",
        cone_band="B"
    )
    print(f"  ✓ Overall: {result['overall']}")
    print(f"  ✓ Findings: {len(result['findings'])} rule(s) triggered")
    for finding in result['findings'][:2]:
        print(f"    • {finding['rule_id']}: {finding['message'][:60]}...")
    assert result['overall'] in ("allowed", "flagged", "blocked")


def test_legal_check_fl():
    """Run check for US:FL jurisdiction"""
    print("\n[LEGAL] Running check for US:FL (assignment strategy)...")
    payload = {
        "strategy": "assignment",
        "disclosures": {"complete": False}
    }
    result = legal_service.run_check(
        jurisdiction_key="US:FL",
        subject="deal",
        payload=payload,
        mode="execute"
    )
    print(f"  ✓ Overall: {result['overall']}")
    print(f"  ✓ Next actions: {len(result['next_actions'])} action(s)")
    assert result['overall'] in ("allowed", "flagged", "blocked")


def test_partners_create():
    """Create a partner"""
    print("\n[PARTNERS] Creating partner...")
    payload = {
        "name": "Jane JV Partner",
        "partner_type": "jv_partner",
        "status": "active",
        "tier": "A",
        "email": "jane@example.com",
        "phone": "+1-204-555-0101",
        "location": "Winnipeg, MB",
        "tags": ["wholesale", "manitoba"]
    }
    result = partners_service.create_partner(payload)
    print(f"  ✓ Partner ID: {result['id']}")
    print(f"  ✓ Name: {result['name']}, Tier: {result['tier']}")
    assert "pt_" in result['id'], "Expected partner ID with pt_ prefix"
    return result['id']


def test_partners_list():
    """List partners"""
    print("\n[PARTNERS] Listing partners...")
    items = partners_service.list_partners()
    print(f"  ✓ Found {len(items)} partner(s)")
    for item in items[:2]:
        print(f"    • {item['name']} ({item['id']}) - Tier {item['tier']}")


def test_partners_create_note(partner_id: str):
    """Create a note for a partner"""
    print(f"\n[PARTNERS] Creating note for partner {partner_id}...")
    payload = {
        "partner_id": partner_id,
        "title": "Initial Discussion",
        "body": "Discussed terms and structure. Plans to send LOI next week.",
        "visibility": "internal"
    }
    result = partners_service.create_note(payload)
    print(f"  ✓ Note ID: {result['id']}")
    print(f"  ✓ Title: {result['title']}")
    assert "pn_" in result['id'], "Expected note ID with pn_ prefix"


def test_partners_dashboard():
    """Get partners dashboard"""
    print("\n[PARTNERS] Getting dashboard...")
    result = partners_service.dashboard()
    totals = result['totals']
    by_type = result['by_type']
    print(f"  ✓ Total partners: {totals['partners']}")
    print(f"  ✓ Total notes: {totals['notes']}")
    print(f"  ✓ By type: {by_type}")


def test_knowledge_attach(partner_id: str):
    """Attach sources to an entity"""
    print(f"\n[KNOWLEDGE] Attaching sources to partner {partner_id}...")
    payload = {
        "entity_type": "partner",
        "entity_id": partner_id,
        "sources": [
            {
                "source_type": "note",
                "ref": "pn_abc123",
                "title": "Call Recap",
                "snippet": "Discussed 10-15% preferred return"
            },
            {
                "source_type": "doc",
                "ref": "doc_xyz789",
                "title": "JV Agreement",
                "snippet": "Standard terms with custom structure"
            }
        ],
        "tags": ["jv", "winnipeg"]
    }
    result = knowledge_service.attach(
        entity_type=payload["entity_type"],
        entity_id=payload["entity_id"],
        sources=payload["sources"],
        tags=payload["tags"],
        meta={}
    )
    print(f"  ✓ Link ID: {result['id']}")
    print(f"  ✓ Sources attached: {len(result['sources'])}")
    print(f"  ✓ Tags: {result['tags']}")
    assert "kl_" in result['id'], "Expected link ID with kl_ prefix"


def test_knowledge_format_citations_long():
    """Format citations (long style)"""
    print("\n[KNOWLEDGE] Formatting citations (long style)...")
    sources = [
        {
            "source_type": "note",
            "ref": "pn_abc123",
            "title": "Call Recap",
            "snippet": "Discussed 10-15% preferred return"
        },
        {
            "source_type": "doc",
            "ref": "doc_xyz789",
            "title": "JV Agreement",
            "snippet": "Standard terms"
        }
    ]
    result = knowledge_service.format_citations(sources, style="long")
    print(f"  ✓ Generated {len(result)} citation(s):")
    for citation in result:
        print(f"    {citation}")
    assert len(result) == 2, "Expected 2 citations"


def test_knowledge_format_citations_short():
    """Format citations (short style)"""
    print("\n[KNOWLEDGE] Formatting citations (short style)...")
    sources = [
        {
            "source_type": "note",
            "ref": "pn_abc123",
            "title": "Discussion"
        },
        {
            "source_type": "url",
            "ref": "https://example.com",
            "title": "Reference"
        }
    ]
    result = knowledge_service.format_citations(sources, style="short")
    print(f"  ✓ Generated {len(result)} citation(s):")
    for citation in result:
        print(f"    {citation}")
    assert len(result) == 2, "Expected 2 citations"


def test_knowledge_list_links():
    """List knowledge links"""
    print("\n[KNOWLEDGE] Listing links...")
    items = knowledge_service.list_links()
    print(f"  ✓ Found {len(items)} link(s)")
    for item in items[:2]:
        src_count = len(item.get('sources', []))
        print(f"    • {item['entity_type']}:{item['entity_id']} - {src_count} source(s)")


if __name__ == "__main__":
    print("=" * 80)
    print("UNIT TESTS: P-LEGAL-1, P-PARTNER-1, P-KNOW-3")
    print("=" * 80)
    
    # Legal filter tests
    print("\n[SECTION] P-LEGAL-1 Tests")
    print("-" * 80)
    try:
        test_legal_seed_defaults()
        test_legal_get_profiles()
        test_legal_check_mb()
        test_legal_check_fl()
        print("\n[SECTION PASS] P-LEGAL-1 - All tests passed")
        legal_pass = True
    except Exception as e:
        print(f"\n[SECTION FAIL] P-LEGAL-1: {e}")
        legal_pass = False
    
    # Partner tests
    print("\n[SECTION] P-PARTNER-1 Tests")
    print("-" * 80)
    partner_id = None
    try:
        partner_id = test_partners_create()
        test_partners_list()
        test_partners_create_note(partner_id)
        test_partners_dashboard()
        print("\n[SECTION PASS] P-PARTNER-1 - All tests passed")
        partner_pass = True
    except Exception as e:
        print(f"\n[SECTION FAIL] P-PARTNER-1: {e}")
        partner_pass = False
    
    # Knowledge tests
    print("\n[SECTION] P-KNOW-3 Tests")
    print("-" * 80)
    try:
        if partner_id:
            test_knowledge_attach(partner_id)
        test_knowledge_format_citations_long()
        test_knowledge_format_citations_short()
        test_knowledge_list_links()
        print("\n[SECTION PASS] P-KNOW-3 - All tests passed")
        know_pass = True
    except Exception as e:
        print(f"\n[SECTION FAIL] P-KNOW-3: {e}")
        know_pass = False
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"P-LEGAL-1 (Legal Filter):    {'PASS' if legal_pass else 'FAIL'}")
    print(f"P-PARTNER-1 (Partners):       {'PASS' if partner_pass else 'FAIL'}")
    print(f"P-KNOW-3 (Knowledge):         {'PASS' if know_pass else 'FAIL'}")
    print(f"\nOverall: {'ALL SYSTEMS OPERATIONAL' if all([legal_pass, partner_pass, know_pass]) else 'SOME FAILURES'}")
    print("=" * 80)
    
    if all([legal_pass, partner_pass, know_pass]):
        sys.exit(0)
    else:
        sys.exit(1)
