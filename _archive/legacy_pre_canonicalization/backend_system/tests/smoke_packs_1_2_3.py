#!/usr/bin/env python3
"""
Smoke tests for PACK 1 (Comms), PACK 2 (JV), and PACK 3 (Property)

Run with: python backend/tests/smoke_packs_1_2_3.py
"""

import json
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_comms():
    """Test PACK 1 - Communication Hub"""
    print("\n" + "="*60)
    print("PACK 1 - P-COMMS-1 (Communication Hub)")
    print("="*60)
    
    try:
        from backend.app.core_gov.comms import service as comms_service
        from backend.app.core_gov.comms.schemas import DraftCreate, SendLogCreate
        
        # Create a draft
        draft_payload = {
            "channel": "sms",
            "subject": "Test Subject",
            "to": "+1234567890",
            "body": "Test message body",
            "deal_id": "deal_001",
            "contact_id": "contact_001",
            "tone": "friendly",
            "tags": ["urgent", "test"],
        }
        draft = comms_service.create_draft(draft_payload)
        print(f"✓ Created draft: {draft['id']}")
        assert draft["body"] == "Test message body"
        
        # List drafts
        drafts = comms_service.list_drafts()
        print(f"✓ Listed {len(drafts)} draft(s)")
        
        # Get draft
        retrieved = comms_service.get_draft(draft["id"])
        print(f"✓ Retrieved draft: {retrieved['id']}")
        assert retrieved["id"] == draft["id"]
        
        # Patch draft
        patched = comms_service.patch_draft(draft["id"], {"status": "ready"})
        print(f"✓ Patched draft status to: {patched['status']}")
        assert patched["status"] == "ready"
        
        # Mark sent
        sent_log = comms_service.mark_sent(draft["id"], provider="twilio", provider_ref="msg_123")
        print(f"✓ Marked sent, sendlog id: {sent_log['id']}")
        assert sent_log["draft_id"] == draft["id"]
        
        # List sendlog
        sendlog = comms_service.list_sendlog(limit=10)
        print(f"✓ Listed {len(sendlog)} sendlog entry(ies)")
        
        print("\n✅ PACK 1 ALL TESTS PASSED")
        return True
    except Exception as e:
        print(f"\n❌ PACK 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_jv():
    """Test PACK 2 - Partner/JV Manager"""
    print("\n" + "="*60)
    print("PACK 2 - P-JV-1 (Partner/JV Manager)")
    print("="*60)
    
    try:
        from backend.app.core_gov.jv import service as jv_service
        from backend.app.core_gov.jv.schemas import PartnerCreate, DealLinkCreate
        
        # Create partner
        partner_payload = {
            "name": "Acme Development Partners",
            "role": "jv_partner",
            "status": "active",
            "email": "contact@acme.com",
            "phone": "+1987654321",
            "notes": "Primary JV partner",
            "tags": ["tier-1", "reliable"],
        }
        partner = jv_service.create_partner(partner_payload)
        print(f"✓ Created partner: {partner['id']}")
        assert partner["name"] == "Acme Development Partners"
        
        # List partners
        partners = jv_service.list_partners()
        print(f"✓ Listed {len(partners)} partner(s)")
        
        # Get partner
        retrieved = jv_service.get_partner(partner["id"])
        print(f"✓ Retrieved partner: {retrieved['id']}")
        
        # Patch partner
        patched = jv_service.patch_partner(partner["id"], {"status": "paused"})
        print(f"✓ Patched partner status to: {patched['status']}")
        assert patched["status"] == "paused"
        
        # Re-activate for link test
        jv_service.patch_partner(partner["id"], {"status": "active"})
        
        # Create link
        link_payload = {
            "partner_id": partner["id"],
            "deal_id": "deal_999",
            "relationship": "JV",
            "split_notes": "50/50 split on profit",
            "status": "active",
        }
        link = jv_service.create_link(link_payload)
        print(f"✓ Created link: {link['id']}")
        assert link["partner_id"] == partner["id"]
        
        # List links
        links = jv_service.list_links(partner_id=partner["id"])
        print(f"✓ Listed {len(links)} link(s) for partner")
        
        # Patch link
        patched_link = jv_service.patch_link(link["id"], {"split_notes": "60/40 split updated"})
        print(f"✓ Patched link: {patched_link['id']}")
        
        # Dashboard
        dashboard = jv_service.dashboard(partner["id"])
        print(f"✓ Dashboard loaded for partner with {len(dashboard['links'])} link(s)")
        assert dashboard["partner"]["id"] == partner["id"]
        
        print("\n✅ PACK 2 ALL TESTS PASSED")
        return True
    except Exception as e:
        print(f"\n❌ PACK 2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_property():
    """Test PACK 3 - Property Intel"""
    print("\n" + "="*60)
    print("PACK 3 - P-PROPERTY-1 (Property Intel Scaffolding)")
    print("="*60)
    
    try:
        from backend.app.core_gov.property import service as prop_service
        from backend.app.core_gov.property.schemas import PropertyCreate, CompsRequest
        
        # Create property
        prop_payload = {
            "address": "123 Main St",
            "country": "CA",
            "region": "ON",
            "city": "Toronto",
            "postal": "M5V 3A8",
            "status": "tracked",
            "deal_id": "deal_888",
        }
        prop = prop_service.create_property(prop_payload)
        print(f"✓ Created property: {prop['id']}")
        assert prop["address"] == "123 Main St"
        assert prop["country"] == "CA"
        
        # List properties
        props = prop_service.list_properties()
        print(f"✓ Listed {len(props)} propert(ies)")
        
        # Get property
        retrieved = prop_service.get_property(prop["id"])
        print(f"✓ Retrieved property: {retrieved['id']}")
        
        # Patch property
        patched = prop_service.patch_property(prop["id"], {"status": "analyzing"})
        print(f"✓ Patched property status to: {patched['status']}")
        assert patched["status"] == "analyzing"
        
        # Neighborhood rating
        rating = prop_service.upsert_rating(
            prop["id"],
            score=85,
            notes="Great neighborhood",
            factors={"walkability": 9, "transit": 8, "schools": 9}
        )
        print(f"✓ Upserted neighborhood rating: score={rating['score']}")
        assert rating["score"] == 85
        
        # Get rating
        retrieved_rating = prop_service.get_rating(prop["id"])
        print(f"✓ Retrieved rating: {retrieved_rating['score']}")
        
        # Save comps stub
        comps = prop_service.save_comps_stub(
            prop["id"],
            radius_km=2.0,
            beds=3,
            baths=2,
            notes="Looking for similar 3BR/2BA"
        )
        print(f"✓ Saved comps stub: {len(comps['comps'])} comps (v1 stub)")
        
        # Get comps
        retrieved_comps = prop_service.get_comps(prop["id"])
        print(f"✓ Retrieved comps: {retrieved_comps is not None}")
        
        # Repair/rent
        rr = prop_service.upsert_repair_rent(
            prop["id"],
            est_repairs=25000.0,
            est_rent=2500.0,
            assumptions={"cap_rate": 0.06, "exit_year": 5}
        )
        print(f"✓ Upserted repair/rent: repairs=${rr['est_repairs']:.0f}, rent=${rr['est_rent']:.0f}")
        
        # Get repair/rent
        retrieved_rr = prop_service.get_repair_rent(prop["id"])
        print(f"✓ Retrieved repair/rent: {retrieved_rr is not None}")
        
        print("\n✅ PACK 3 ALL TESTS PASSED")
        return True
    except Exception as e:
        print(f"\n❌ PACK 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "#"*60)
    print("# SMOKE TESTS: PACK 1, PACK 2, PACK 3")
    print("#"*60)
    
    results = {
        "PACK 1 - Comms": test_comms(),
        "PACK 2 - JV": test_jv(),
        "PACK 3 - Property": test_property(),
    }
    
    print("\n" + "#"*60)
    print("# SUMMARY")
    print("#"*60)
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 ALL PACKS VALIDATED SUCCESSFULLY!")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED - CHECK OUTPUT ABOVE")
        return 1


if __name__ == "__main__":
    sys.exit(main())
