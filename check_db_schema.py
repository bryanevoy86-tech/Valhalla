#!/usr/bin/env python3
"""
Check actual database schema
"""
import sqlite3
from pathlib import Path

db_file = Path(__file__).parent / "valhalla_local.db"

if not db_file.exists():
    print(f"Database not found: {db_file}")
    exit(1)

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("="*80)
print("TABLES IN DATABASE:")
print("="*80)
for table in sorted(tables):
    print(f"  {table[0]}")

print("\n" + "="*80)
print("DEALS TABLE SCHEMA:")
print("="*80)

try:
    cursor.execute("PRAGMA table_info(deals);")
    columns = cursor.fetchall()
    for col in columns:
        cid, name, col_type, notnull, dflt_value, pk = col
        print(f"  {name:20} {col_type:15} {'NOT NULL' if notnull else 'nullable':10}")
except:
    print("  'deals' table does not exist")

print("\n" + "="*80)
print("CHECKING FOR RELATED TABLES:")
print("="*80)

for table_name in ["deal", "lead", "offer", "buyer", "audit_event", "audit_events"]:
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%{table_name}%';")
    results = cursor.fetchall()
    if results:
        print(f"  Found tables matching '{table_name}': {[r[0] for r in results]}")

conn.close()
