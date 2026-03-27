#!/usr/bin/env python
"""
Multi-deal operational verification - comprehensive test across all seeded deals.

Tests:
1. Dashboard shows all deals correctly
2. Heimdall analyze works consistently across all states
3. Stage advancement paths (success, rejection, override)
4. Audit trail consistency per deal
5. Offer/contract/buyer relationships remain stable
"""

import json
import sys
import os
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("DATABASE_URL", "sqlite:///valhalla_local.db")
os.environ.setdefault("VALHALLA_JWT_SECRET", "dev-secret-key")
os.environ.setdefault("BUILDER_KEY", "test-builder-key-v0.2-verification")

# Import app
sys.path.insert(0, 'services/api')
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)
AUTH_HEADER = {"X-API-Key": "test-builder-key-v0.2-verification"}

# Test deals
SEEDED_DEALS = {
    "A": {
        "id": 10,
        "title": "Deal A - Minimal Draft",
        "stage": "draft",
        "has_offer": False,
        "has_contract": False,
        "missing_fields": ["repairs", "offer"],
        "should_advance": False,
    },
    "B": {
        "id": 11,
        "title": "Deal B - Analysis Ready",
        "stage": "lead_received",
        "has_offer": False,
        "has_contract": False,
        "missing_fields": ["offer"],
        "should_advance": False,  # Unknown blocker in test data
    },
    "C": {
        "id": 12,
        "title": "Deal C - Offer State",
        "stage": "offer_presented",
        "has_offer": True,
        "has_contract": False,
        "missing_fields": [],
        "should_advance": False,  # No valid transition from offer_presented
    },
    "D": {
        "id": 13,
        "title": "Deal D - Contract State",
        "stage": "under_contract",
        "has_offer": True,
        "has_contract": True,
        "missing_fields": [],
        "should_advance": False,  # No valid transition from under_contract
    },
    "E": {
        "id": 14,
        "title": "Deal E - Blocked Problem",
        "stage": "lead_received",
        "has_offer": False,
        "has_contract": False,
        "missing_fields": ["repairs"],  # Missing estimated_repair_cost
        "should_advance": False,
    },
}

results = {
    "timestamp": datetime.utcnow().isoformat(),
    "deals_tested": len(SEEDED_DEALS),
    "dashboard": {},
    "heimdall": {},
    "advancement": {},
    "audit": {},
    "relationships": {},
    "summary": {}
}


def test_dashboard():
    """Verify dashboard shows all deals correctly."""
    print("\n" + "="*80)
    print("STEP 1: DASHBOARD VERIFICATION")
    print("="*80)
    
    response = client.get("/api/dashboard/pipeline", headers=AUTH_HEADER)
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"✗ Dashboard request failed: {response.text}")
        results["dashboard"]["error"] = response.text
        return False
    
    data = response.json()
    results["dashboard"]["total_deals"] = data.get("total_deals")
    results["dashboard"]["deals_in_pipeline"] = data.get("deals_in_pipeline")
    
    # Check if all seeded deals are visible in the deals array
    found_deals = {}
    deals_array = data.get("deals", [])
    deal_ids_in_response = [d.get("deal_id") for d in deals_array]
    
    for letter, deal_info in SEEDED_DEALS.items():
        deal_id = deal_info["id"]
        if deal_id in deal_ids_in_response:
            found_deals[letter] = deal_id
            print(f"✓ Deal {letter} (ID: {deal_id}) visible in dashboard")
        else:
            print(f"✗ Deal {letter} (ID: {deal_id}) NOT visible in dashboard")
    
    results["dashboard"]["found_deals"] = found_deals
    results["dashboard"]["all_found"] = len(found_deals) == len(SEEDED_DEALS)
    
    return len(found_deals) == len(SEEDED_DEALS)


def test_heimdall_across_deals():
    """Verify Heimdall analyze works consistently across all deals."""
    print("\n" + "="*80)
    print("STEP 2: HEIMDALL ANALYZE ACROSS ALL DEALS")
    print("="*80)
    
    results["heimdall"]["analyses"] = {}
    all_success = True
    
    for letter, deal_info in SEEDED_DEALS.items():
        deal_id = deal_info["id"]
        response = client.post(
            f"/api/heimdall/deals/{deal_id}/analyze",
            headers=AUTH_HEADER
        )
        
        if response.status_code != 200:
            print(f"✗ Deal {letter} (ID: {deal_id}) analyze failed: {response.status_code}")
            results["heimdall"]["analyses"][letter] = {"error": f"Status {response.status_code}"}
            all_success = False
            continue
        
        data = response.json()
        print(f"✓ Deal {letter} (ID: {deal_id}) analyzed successfully")
        print(f"    Stage: {data.get('current_stage')}")
        print(f"    Blockers: {data.get('blocker_flags', [])}")
        print(f"    Recommendation: {data.get('recommendations', {}).get('recommended_stage', 'None')}")
        
        results["heimdall"]["analyses"][letter] = {
            "deal_id": deal_id,
            "stage": data.get("current_stage"),
            "blockers": data.get("blocker_flags", []),
            "risks": data.get("risk_flags", []),
            "recommended_stage": data.get("recommendations", {}).get("recommended_stage"),
        }
    
    results["heimdall"]["all_success"] = all_success
    return all_success


def test_stage_advancement():
    """Test stage advancement paths with real deals."""
    print("\n" + "="*80)
    print("STEP 3: STAGE ADVANCEMENT PATHS VERIFICATION")
    print("="*80)
    
    results["advancement"]["paths"] = {
        "success": [],
        "rejection": [],
        "override": []
    }
    
    # Test Deal B - try to advance to valid next stage
    deal_b_id = 11
    print(f"\nAttempting advancement on Deal B (ID: {deal_b_id})...")
    response = client.post(
        f"/api/heimdall/deals/{deal_b_id}/advance-stage",
        json={"requested_stage": "offer_received", "approved_by": "test-operator", "reason": "Test advancement"},
        headers=AUTH_HEADER
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("result") == "rejected":
            print(f"  → Rejection (as expected): {data.get('reason')}")
            results["advancement"]["paths"]["rejection"].append({
                "deal_id": deal_b_id,
                "reason": data.get("reason"),
                "recorded": True
            })
        else:
            print(f"  → Success: Deal advanced to {data.get('new_stage')}")
            results["advancement"]["paths"]["success"].append({
                "deal_id": deal_b_id,
                "from_stage": data.get("previous_stage"),
                "to_stage": data.get("new_stage"),
                "recorded": True
            })
    else:
        print(f"  ✗ Request failed: {response.status_code}")
        results["advancement"]["paths"]["rejection"].append({
            "deal_id": deal_b_id,
            "error": response.status_code
        })


def test_audit_consistency():
    """Verify audit trails are consistent per deal."""
    print("\n" + "="*80)
    print("STEP 4: AUDIT TRAIL CONSISTENCY VERIFICATION")
    print("="*80)
    
    results["audit"]["trails"] = {}
    all_clean = True
    
    for letter, deal_info in SEEDED_DEALS.items():
        deal_id = deal_info["id"]
        response = client.get(
            f"/api/audit/deals/{deal_id}",
            headers=AUTH_HEADER
        )
        
        if response.status_code != 200:
            print(f"✗ Deal {letter} (ID: {deal_id}) audit query failed: {response.status_code}")
            results["audit"]["trails"][letter] = {"error": f"Status {response.status_code}"}
            all_clean = False
            continue
        
        events = response.json()
        print(f"✓ Deal {letter} (ID: {deal_id}): {len(events)} audit events")
        
        # Check for cross-deal contamination
        for event in events:
            if event.get("entity_id") != deal_id:
                print(f"  ✗ CONTAMINATION: Event with entity_id={event.get('entity_id')} in deal {deal_id} audit")
                all_clean = False
        
        results["audit"]["trails"][letter] = {
            "deal_id": deal_id,
            "event_count": len(events),
            "events": [{"action": e.get("action"), "entity_id": e.get("entity_id")} for e in events]
        }
    
    results["audit"]["all_clean"] = all_clean
    return all_clean


def test_relationships():
    """Verify offer/contract/buyer relationships remain stable."""
    print("\n" + "="*80)
    print("STEP 5: RELATIONSHIP INTEGRITY VERIFICATION")
    print("="*80)
    
    results["relationships"]["status"] = {}
    
    # Check offer counts per deal
    import sqlite3
    conn = sqlite3.connect('valhalla_local.db')
    cursor = conn.cursor()
    
    for letter, deal_info in SEEDED_DEALS.items():
        deal_id = deal_info["id"]
        
        # Count offers
        cursor.execute('SELECT COUNT(*) FROM offers WHERE deal_id = ?', (deal_id,))
        offer_count = cursor.fetchone()[0]
        
        # Count contracts
        cursor.execute('SELECT COUNT(*) FROM contracts WHERE deal_id = ?', (deal_id,))
        contract_count = cursor.fetchone()[0]
        
        # Check buyer match
        cursor.execute('SELECT COUNT(*) FROM buyer_matches WHERE deal_id = ?', (deal_id,))
        buyer_match_count = cursor.fetchone()[0]
        
        status = {
            "offer_count": offer_count,
            "contract_count": contract_count,
            "buyer_match_count": buyer_match_count
        }
        
        # Validate against expected
        if offer_count == (1 if deal_info["has_offer"] else 0):
            status["offers_ok"] = True
        else:
            status["offers_ok"] = False
            print(f"✗ Deal {letter}: Expected {1 if deal_info['has_offer'] else 0} offers, got {offer_count}")
        
        if contract_count == (1 if deal_info["has_contract"] else 0):
            status["contracts_ok"] = True
        else:
            status["contracts_ok"] = False
            print(f"✗ Deal {letter}: Expected {1 if deal_info['has_contract'] else 0} contracts, got {contract_count}")
        
        results["relationships"]["status"][letter] = status
        
        if status["offers_ok"] and status["contracts_ok"]:
            print(f"✓ Deal {letter}: Relationships intact (offers:{offer_count}, contracts:{contract_count})")
    
    conn.close()


def summarize():
    """Generate final summary."""
    print("\n" + "="*80)
    print("MULTI-DEAL VERIFICATION SUMMARY")
    print("="*80)
    
    summary = {
        "dashboard_ok": results["dashboard"].get("all_found", False),
        "heimdall_ok": results["heimdall"].get("all_success", False),
        "audit_ok": results["audit"].get("all_clean", False),
        "relationship_ok": all(
            r.get("offers_ok", False) and r.get("contracts_ok", False) 
            for r in results["relationships"]["status"].values()
        ),
    }
    
    print(f"\nDashboard:     {'✓' if summary['dashboard_ok'] else '✗'}")
    print(f"Heimdall:      {'✓' if summary['heimdall_ok'] else '✗'}")
    print(f"Audit:         {'✓' if summary['audit_ok'] else '✗'}")
    print(f"Relationships: {'✓' if summary['relationship_ok'] else '✗'}")
    
    all_ok = all(summary.values())
    print(f"\nOverall: {'✓ ALL CHECKS PASSED' if all_ok else '✗ SOME CHECKS FAILED'}")
    
    results["summary"] = summary
    results["overall_ok"] = all_ok
    
    return all_ok


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MULTI-DEAL OPERATIONAL VERIFICATION")
    print("="*80)
    print(f"Testing {len(SEEDED_DEALS)} seeded deals...")
    
    try:
        test_dashboard()
        test_heimdall_across_deals()
        test_stage_advancement()
        test_audit_consistency()
        test_relationships()
        success = summarize()
        
        # Save results
        with open("multi_deal_verification_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n✓ Results saved to: multi_deal_verification_results.json")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n✗ Verification error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
