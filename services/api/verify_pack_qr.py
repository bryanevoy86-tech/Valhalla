# Verify PACK Q and PACK R endpoints

from app.main import app

print("=== PACK Q: Internal Auditor ===")
print("Prefix: /audit")
print()
print("Endpoints:")
print("  POST   /audit/scan/deal/{deal_id}")
print("  GET    /audit/summary")
print("  GET    /audit/events/open")
print("  GET    /audit/events/deal/{deal_id}")
print("  POST   /audit/events/{event_id}/resolve")
print()

print("=== PACK R: Governance Decisions ===")
print("Prefix: /governance/decisions")
print()
print("Endpoints:")
print("  POST   /governance/decisions/")
print("  GET    /governance/decisions/{decision_id}")
print("  GET    /governance/decisions/subject/{subject_type}/{subject_id}")
print("  GET    /governance/decisions/subject/{subject_type}/{subject_id}/latest-final")
print("  GET    /governance/decisions/by-role/{role}")
print()

# Count total routes
audit_routes = [r for r in app.routes if hasattr(r, 'path') and '/audit' in r.path]
gov_routes = [r for r in app.routes if hasattr(r, 'path') and '/governance/decisions' in r.path]

print(f"✓ PACK Q: {len(audit_routes)} routes registered")
print(f"✓ PACK R: {len(gov_routes)} routes registered")
print(f"✓ Total application routes: {len([r for r in app.routes])}")
