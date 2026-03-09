#!/usr/bin/env python
"""Test edge-case file handling"""
import csv
import json

print("="*70)
print("EDGE-CASE RESILIENCE TEST")
print("="*70)

# Test 1: Malformed CSV
print("\n[TEST 1] edge_case_bad_csv.csv (incomplete row)")
try:
    with open('data/inbox/real_leads/edge_case_bad_csv.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f"  ✓ Read successfully: {len(rows)} rows (CSV tolerated incomplete row)")
    for i, row in enumerate(rows):
        print(f"    Row {i+1}: {row}")
except Exception as e:
    print(f"  ✗ EXCEPTION: {type(e).__name__}: {e}")

# Test 2: Malformed JSON
print("\n[TEST 2] edge_case_bad_json.json (invalid syntax)")
try:
    with open('data/inbox/real_leads/edge_case_bad_json.json', 'r') as f:
        data = json.load(f)
    print(f"  ✓ Read successfully: {len(data)} records")
except json.JSONDecodeError as e:
    print(f"  ✓ CAUGHT: json.JSONDecodeError (expected) - {str(e)[:60]}...")
except Exception as e:
    print(f"  ? UNEXPECTED: {type(e).__name__}: {e}")

# Test 3: Duplicates
print("\n[TEST 3] edge_case_duplicates.csv (duplicate IDs)")
try:
    with open('data/inbox/real_leads/edge_case_duplicates.csv', 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    ids = [row.get('lead_id') for row in rows]
    unique_ids = set(ids)
    print(f"  ✓ Read successfully: {len(rows)} rows, {len(unique_ids)} unique IDs")
    if len(ids) != len(unique_ids):
        dupes = {id for id in unique_ids if ids.count(id) > 1}
        print(f"    Duplicates detected: {dupes}")
except Exception as e:
    print(f"  ✗ EXCEPTION: {type(e).__name__}: {e}")

print("\n" + "="*70)
print("EDGE-CASE TEST COMPLETE")
print("="*70)
