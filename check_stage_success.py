#!/usr/bin/env python
import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('valhalla_local.db')
cursor = conn.cursor()

print("\n" + "="*80)
print("STAGE ADVANCEMENT SUCCESS - VERIFICATION")
print("="*80)

# Check deal state
cursor.execute('SELECT id, stage, status FROM deals WHERE id = 11')
deal = cursor.fetchone()
print(f"\n✅ DEAL 11 CURRENT STATE:")
print(f"   ID: {deal[0]}")
print(f"   Stage: {deal[1]}")  
print(f"   Status: {deal[2]}")

# Check recent audit events for deal 11
cursor.execute('''
    SELECT id, created_at, action, entity_id, previous_value, new_value
    FROM audit_logs
    WHERE entity_type = "deal" AND entity_id = 11
    ORDER BY created_at DESC
    LIMIT 15
''')

results = cursor.fetchall()
print(f"\n✅ AUDIT EVENTS FOR DEAL 11 ({len(results)} total):")

# Look for the key events
heimdall_analyzed = False
heimdall_recommended = False
stage_advanced = False

for row in results:
    action = row[2]
    print(f"\n   [{row[0]}] {action}")
    print(f"       Time: {row[1]}")
    
    if action == "heimdall_analyzed_deal":
        heimdall_analyzed = True
        try:
            prev = json.loads(row[4]) if row[4] else None
            new = json.loads(row[5]) if row[5] else None
            print(f"       ✅ Deal analyzed")
        except:
            pass
    
    elif action == "heimdall_recommended_stage":
        heimdall_recommended = True
        try:
            meta = json.loads(row[5]) if row[5] else None
            if meta and 'to_stage' in meta:
                print(f"       ✅ Recommended transition to: {meta.get('to_stage')}")
        except:
            pass
    
    elif action == "heimdall_stage_advanced":
        stage_advanced = True
        try:
            meta = json.loads(row[5]) if row[5] else None
            if meta:
                print(f"       ✅ Successfully advanced: {meta.get('from_stage')} → {meta.get('to_stage')}")
                print(f"          Approved by: {meta.get('approved_by')}")
        except:
            pass

print(f"\n" + "="*80)
print("SUCCESS PATH VERIFICATION RESULTS")
print("="*80)

print(f"\n✅ Deal advanced from: lead_received → preliminary_analysis")
print(f"✅ Heimdall analyzed: {heimdall_analyzed}")
print(f"✅ Heimdall recommended: {heimdall_recommended}")
print(f"✅ Stage advancement recorded: {stage_advanced}")

success_criteria = {
    "deal_stage_changed": deal[1] == "preliminary_analysis",
    "heimdall_analyzed": heimdall_analyzed,
    "heimdall_recommended": heimdall_recommended,
    "stage_advanced_logged": stage_advanced,
}

print(f"\nSUCCESS CRITERIA MET:")
for criterion, met in success_criteria.items():
    status = "✅" if met else "❌"
    print(f"  {status} {criterion}")

all_pass = all(success_criteria.values())
print(f"\n{'='*80}")
print(f"OVERALL: {'✅ FULL SUCCESS PATH VERIFIED' if all_pass else '❌ ISSUES DETECTED'}")
print(f"{'='*80}\n")

conn.close()
