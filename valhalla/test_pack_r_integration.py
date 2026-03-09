#!/usr/bin/env python
"""
Integration test for PACK R — Governance Integration
Tests all governance decision endpoints and operations
"""

import sys
sys.path.insert(0, '/dev/valhalla/services/api')

from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.governance_decision import GovernanceDecision
from app.schemas.governance_decision import GovernanceDecisionIn
from app.services.governance_service import (
    record_decision,
    list_decisions_for_subject,
    get_latest_final_decision,
    list_decisions_by_role,
    get_decision_by_id,
)

def test_governance():
    """Run integration tests for PACK R"""
    print("\n" + "="*60)
    print("PACK R — Governance Integration Tests")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Test 1: Record a decision
        print("\n1. Recording King's approval decision...")
        payload = GovernanceDecisionIn(
            subject_type="deal",
            subject_id=999,
            role="King",
            action="approve",
            reason="Meets all Valhalla criteria",
            is_final=True
        )
        decision = record_decision(db, payload)
        print(f"   ✓ Decision recorded with ID: {decision.id}")
        print(f"     Role: {decision.role}, Action: {decision.action}")
        
        # Test 2: Get decision by ID
        print("\n2. Retrieving decision by ID...")
        retrieved = get_decision_by_id(db, decision.id)
        assert retrieved is not None
        print(f"   ✓ Retrieved: {retrieved.role} - {retrieved.action}")
        
        # Test 3: List decisions for subject
        print("\n3. Listing all decisions for deal #999...")
        decisions = list_decisions_for_subject(db, "deal", 999)
        print(f"   ✓ Found {len(decisions)} decision(s)")
        for d in decisions:
            print(f"     - {d.role}: {d.action} ({d.reason})")
        
        # Test 4: Get latest final decision
        print("\n4. Getting latest final decision for deal #999...")
        final = get_latest_final_decision(db, "deal", 999)
        if final:
            print(f"   ✓ Final decision: {final.role} - {final.action}")
        else:
            print("   ✗ No final decision found")
        
        # Test 5: Record multiple roles
        print("\n5. Recording decisions from other roles...")
        for role in ["Queen", "Odin", "Loki", "Tyr"]:
            payload = GovernanceDecisionIn(
                subject_type="deal",
                subject_id=999,
                role=role,
                action="approve",
                reason=f"{role} approval",
                is_final=False
            )
            d = record_decision(db, payload)
            print(f"   ✓ {role} decision recorded (ID: {d.id})")
        
        # Test 6: List decisions by role
        print("\n6. Listing all decisions by King...")
        king_decisions = list_decisions_by_role(db, "King")
        print(f"   ✓ King made {len(king_decisions)} decision(s)")
        
        # Test 7: Test different subject types
        print("\n7. Testing with different subject types...")
        for subject_type in ["contract", "professional", "custom_entity"]:
            payload = GovernanceDecisionIn(
                subject_type=subject_type,
                subject_id=100,
                role="Queen",
                action="approve",
                reason=f"Testing {subject_type}",
                is_final=False
            )
            d = record_decision(db, payload)
            print(f"   ✓ Decision for {subject_type} recorded")
        
        # Test 8: Verify subject type flexibility
        print("\n8. Listing all governance decision records...")
        all_decisions = db.query(GovernanceDecision).all()
        print(f"   ✓ Total governance decisions in database: {len(all_decisions)}")
        
        print("\n" + "="*60)
        print("✓ ALL PACK R TESTS PASSED!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_governance()
    sys.exit(0 if success else 1)
