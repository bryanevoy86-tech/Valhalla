# Integration test for PACK Q and PACK R

# Import models first to ensure proper SQLAlchemy initialization
import app.models  # noqa: F401

from app.core.db import SessionLocal
from app.services.internal_auditor import scan_deal, list_open_events, resolve_audit_event
from app.services.governance_service import record_decision, list_decisions_for_subject
from app.schemas.governance_decision import GovernanceDecisionIn

print("=== PACK Q + R Integration Test ===\n")

db = SessionLocal()

try:
    # Test PACK Q: Audit a deal
    print("1. Scanning deal #999 for compliance issues...")
    audit_result = scan_deal(db, deal_id=999)
    print(f"   Found {audit_result['issues_found']} issues")
    print(f"   Checklist: {audit_result['checklist']}")
    
    # List open events
    print("\n2. Listing all open audit events...")
    open_events = list_open_events(db)
    print(f"   Total open events: {len(open_events)}")
    
    # Test PACK R: Record a governance decision
    print("\n3. Recording King's approval decision...")
    decision_payload = GovernanceDecisionIn(
        subject_type="deal",
        subject_id=999,
        role="King",
        action="approve",
        reason="Meets all Valhalla criteria",
        is_final=True
    )
    decision = record_decision(db, decision_payload)
    print(f"   Decision ID: {decision.id}")
    print(f"   Role: {decision.role}, Action: {decision.action}")
    
    # List decisions for the deal
    print("\n4. Listing all decisions for deal #999...")
    decisions = list_decisions_for_subject(db, "deal", 999)
    print(f"   Total decisions: {len(decisions)}")
    for dec in decisions:
        print(f"   - {dec.role}: {dec.action} ({dec.reason})")
    
    # Resolve an audit event if any exist
    if audit_result['events']:
        event_id = audit_result['events'][0]['id']
        print(f"\n5. Resolving audit event #{event_id}...")
        resolved = resolve_audit_event(db, event_id)
        if resolved:
            print(f"   ✓ Event resolved at {resolved.resolved_at}")
    
    print("\n✓ All PACK Q + R operations successful!")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    db.close()
