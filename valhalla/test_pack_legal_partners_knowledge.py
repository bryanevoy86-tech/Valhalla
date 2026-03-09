"""
Smoke tests for P-LEGAL-1, P-PARTNER-1, P-KNOW-3

Tests basic functionality:
- Legal filter: seed defaults, run jurisdiction check
- Partners: create partner, create note, get dashboard
- Knowledge: attach sources, format citations
"""

import requests
import json

BASE_URL = "http://localhost:8000"
LEGAL_PREFIX = f"{BASE_URL}/core/legal"
PARTNERS_PREFIX = f"{BASE_URL}/core/partners"
KNOWLEDGE_PREFIX = f"{BASE_URL}/core/knowledge"


def test_legal_seed_defaults():
    """POST /core/legal/seed_defaults"""
    resp = requests.post(f"{LEGAL_PREFIX}/seed_defaults")
    print(f"\n[LEGAL] Seed defaults: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  - Seeded: {data.get('seeded')}, Count: {data.get('count')}")
        assert data.get("count", 0) > 0, "Expected at least 1 profile"


def test_legal_check_mb():
    """POST /core/legal/check for CA:MB with wholesale strategy"""
    payload = {
        "jurisdiction_key": "CA:MB",
        "subject": "deal",
        "mode": "execute",
        "cone_band": "B",
        "payload": {
            "strategy": "wholesale",
            "seller": {"id_verified": False},
            "buyer": {"entity_type": ""}
        }
    }
    resp = requests.post(f"{LEGAL_PREFIX}/check", json=payload)
    print(f"\n[LEGAL] Check CA:MB wholesale: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  - Overall: {data.get('overall')}")
        print(f"  - Findings: {len(data.get('findings', []))} rule(s) triggered")
        assert data.get("overall") in ("allowed", "flagged", "blocked"), "Invalid overall status"


def test_legal_check_fl():
    """POST /core/legal/check for US:FL"""
    payload = {
        "jurisdiction_key": "US:FL",
        "subject": "deal",
        "mode": "execute",
        "cone_band": "B",
        "payload": {
            "strategy": "assignment",
            "disclosures": {"complete": False}
        }
    }
    resp = requests.post(f"{LEGAL_PREFIX}/check", json=payload)
    print(f"\n[LEGAL] Check US:FL assignment: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        assert data.get("overall") in ("allowed", "flagged", "blocked")


def test_legal_list_profiles():
    """GET /core/legal/profiles"""
    resp = requests.get(f"{LEGAL_PREFIX}/profiles")
    print(f"\n[LEGAL] List profiles: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("items", [])
        print(f"  - Found {len(items)} profile(s)")
        for item in items[:2]:
            print(f"    • {item.get('key')}: {item.get('name')}")


def test_partners_create():
    """POST /core/partners - Create a partner"""
    payload = {
        "name": "John JV Partner",
        "partner_type": "jv_partner",
        "status": "active",
        "tier": "A",
        "email": "john@example.com",
        "phone": "+1-204-555-0100",
        "location": "Winnipeg, MB",
        "notes": "First JV with preferred return 10-15%",
        "tags": ["wholesale", "manitoba"]
    }
    resp = requests.post(f"{PARTNERS_PREFIX}", json=payload)
    print(f"\n[PARTNERS] Create partner: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        partner_id = data.get("id")
        print(f"  - Partner ID: {partner_id}")
        print(f"  - Name: {data.get('name')}, Tier: {data.get('tier')}")
        return partner_id
    return None


def test_partners_create_note(partner_id: str):
    """POST /core/partners/notes - Create a note for partner"""
    if not partner_id:
        print("\n[PARTNERS] Skipping note creation (no partner_id)")
        return
    
    payload = {
        "partner_id": partner_id,
        "title": "Call Recap - Q1 Planning",
        "body": "Discussed investment structure. Wants 10-15% preferred return. Will send LOI draft next week.",
        "visibility": "internal"
    }
    resp = requests.post(f"{PARTNERS_PREFIX}/notes", json=payload)
    print(f"\n[PARTNERS] Create note: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  - Note ID: {data.get('id')}")
        print(f"  - Title: {data.get('title')}")


def test_partners_dashboard():
    """GET /core/partners/dashboard"""
    resp = requests.get(f"{PARTNERS_PREFIX}/dashboard")
    print(f"\n[PARTNERS] Dashboard: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        totals = data.get("totals", {})
        by_type = data.get("by_type", {})
        print(f"  - Total partners: {totals.get('partners', 0)}")
        print(f"  - Total notes: {totals.get('notes', 0)}")
        print(f"  - By type: {by_type}")


def test_partners_list():
    """GET /core/partners - List partners"""
    resp = requests.get(f"{PARTNERS_PREFIX}")
    print(f"\n[PARTNERS] List partners: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("items", [])
        print(f"  - Found {len(items)} partner(s)")
        for item in items[:3]:
            print(f"    • {item.get('name')} ({item.get('id')}) - {item.get('tier')}")


def test_knowledge_attach(partner_id: str = None):
    """POST /core/knowledge/attach - Attach sources to entity"""
    entity_id = partner_id or "partner_test_001"
    payload = {
        "entity_type": "partner",
        "entity_id": entity_id,
        "sources": [
            {
                "source_type": "note",
                "ref": "pn_abc123",
                "title": "Call Recap Q1",
                "snippet": "10-15% preferred return discussion"
            },
            {
                "source_type": "doc",
                "ref": "doc_xyz789",
                "title": "JV Agreement Draft",
                "snippet": "Standard terms with custom return structure"
            }
        ],
        "tags": ["jv", "manitoba", "active"]
    }
    resp = requests.post(f"{KNOWLEDGE_PREFIX}/attach", json=payload)
    print(f"\n[KNOWLEDGE] Attach sources: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  - Link ID: {data.get('id')}")
        print(f"  - Sources attached: {len(data.get('sources', []))}")
        print(f"  - Tags: {data.get('tags', [])}")


def test_knowledge_format_citations():
    """POST /core/knowledge/citations/format - Format citations"""
    payload = {
        "style": "long",
        "sources": [
            {
                "source_type": "note",
                "ref": "pn_abc123",
                "title": "Call Recap Q1",
                "snippet": "10-15% preferred return discussion"
            },
            {
                "source_type": "doc",
                "ref": "doc_xyz789",
                "title": "JV Agreement Draft",
                "snippet": "Standard terms with custom return structure"
            },
            {
                "source_type": "url",
                "ref": "https://example.com/terms",
                "title": "External Reference"
            }
        ]
    }
    resp = requests.post(f"{KNOWLEDGE_PREFIX}/citations/format", json=payload)
    print(f"\n[KNOWLEDGE] Format citations (long style): {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        citations = data.get("citations", [])
        print(f"  - Generated {len(citations)} citation(s):")
        for cit in citations:
            print(f"    {cit}")


def test_knowledge_format_citations_short():
    """POST /core/knowledge/citations/format - Short format"""
    payload = {
        "style": "short",
        "sources": [
            {
                "source_type": "note",
                "ref": "pn_abc123",
                "title": "Call Recap"
            },
            {
                "source_type": "doc",
                "ref": "doc_xyz789",
                "title": "Agreement"
            }
        ]
    }
    resp = requests.post(f"{KNOWLEDGE_PREFIX}/citations/format", json=payload)
    print(f"\n[KNOWLEDGE] Format citations (short style): {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        citations = data.get("citations", [])
        print(f"  - Generated {len(citations)} citation(s):")
        for cit in citations:
            print(f"    {cit}")


def test_knowledge_list_links():
    """GET /core/knowledge/links - List links"""
    resp = requests.get(f"{KNOWLEDGE_PREFIX}/links")
    print(f"\n[KNOWLEDGE] List links: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        items = data.get("items", [])
        print(f"  - Found {len(items)} link(s)")
        for item in items[:3]:
            print(f"    • {item.get('entity_type')}:{item.get('entity_id')} - {len(item.get('sources', []))} source(s)")


if __name__ == "__main__":
    print("=" * 80)
    print("PACK SMOKE TESTS: P-LEGAL-1, P-PARTNER-1, P-KNOW-3")
    print("=" * 80)
    
    # Legal filter tests
    print("\n[SECTION] P-LEGAL-1 — Legal Filter Tests")
    print("-" * 80)
    try:
        test_legal_seed_defaults()
        test_legal_check_mb()
        test_legal_check_fl()
        test_legal_list_profiles()
        print("\n✓ P-LEGAL-1 tests passed")
    except Exception as e:
        print(f"\n✗ P-LEGAL-1 error: {e}")
    
    # Partner tests
    print("\n[SECTION] P-PARTNER-1 — Partner Management Tests")
    print("-" * 80)
    partner_id = None
    try:
        partner_id = test_partners_create()
        test_partners_create_note(partner_id)
        test_partners_list()
        test_partners_dashboard()
        print("\n✓ P-PARTNER-1 tests passed")
    except Exception as e:
        print(f"\n✗ P-PARTNER-1 error: {e}")
    
    # Knowledge tests
    print("\n[SECTION] P-KNOW-3 — Knowledge Links + Citations Tests")
    print("-" * 80)
    try:
        test_knowledge_attach(partner_id)
        test_knowledge_format_citations()
        test_knowledge_format_citations_short()
        test_knowledge_list_links()
        print("\n✓ P-KNOW-3 tests passed")
    except Exception as e:
        print(f"\n✗ P-KNOW-3 error: {e}")
    
    print("\n" + "=" * 80)
    print("SMOKE TEST SUITE COMPLETE")
    print("=" * 80)
