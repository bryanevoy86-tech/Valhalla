#!/usr/bin/env python
"""Audit migration files for table creation collisions."""

import os
import re
from collections import defaultdict
from pathlib import Path

def extract_table_creates(file_path):
    """Extract all op.create_table() calls from a migration file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Look for op.create_table('table_name' or op.create_table(table_name
    tables = re.findall(r"op\.create_table\(['\"]?(\w+)['\"]?", content)
    return tables

def extract_revision(file_path):
    """Extract revision ID from migration file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Handle both old and new Alembic formats with type hints
    rev_match = re.search(r"^revision\s*(?::\s*[\w\[\],\s.]+)?\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE)
    return rev_match.group(1) if rev_match else None

def audit_tables():
    """Audit table creations across all migrations."""
    versions_dir = Path("alembic/versions")
    
    if not versions_dir.exists():
        print("❌ alembic/versions directory does not exist")
        return False
    
    files = sorted(versions_dir.glob("*.py"))
    files = [f for f in files if f.name != "__init__.py"]
    
    print(f"📊 Scanning {len(files)} migration files for table creations\n")
    
    table_creators = defaultdict(list)
    issues = []
    
    # Scan all files
    for file_path in files:
        revision = extract_revision(file_path)
        if not revision:
            continue
        
        tables = extract_table_creates(file_path)
        for table in tables:
            table_creators[table].append((revision, file_path.name))
    
    # Check for duplicates
    print("🔍 Checking for duplicate table creations:")
    duplicates = {t: creators for t, creators in table_creators.items() if len(creators) > 1}
    
    if duplicates:
        print(f"  ⚠️ Found {len(duplicates)} table(s) created multiple times:\n")
        for table, creators in sorted(duplicates.items()):
            issues.append(f"⚠️ TABLE CREATED MULTIPLE TIMES: '{table}'")
            print(f"  Table '{table}' created in:")
            for revision, filename in creators:
                print(f"    - {filename} (rev: {revision})")
            print()
    else:
        print("  ✅ No duplicate table creations found\n")
    
    # Report all tables created
    print("📋 All tables created by migrations:")
    if table_creators:
        for table in sorted(table_creators.keys()):
            creators = table_creators[table]
            if len(creators) == 1:
                rev, filename = creators[0]
                print(f"  - {table} (created by {filename})")
            else:
                print(f"  - {table} (⚠️ created by {len(creators)} migrations)")
    else:
        print("  ℹ️ No table creations found")
    print()
    
    # Summary
    print("=" * 60)
    if duplicates:
        print(f"⚠️ AUDIT WARNING - {len(duplicates)} table(s) created multiple times\n")
        for table in sorted(duplicates.keys()):
            print(f"  - {table}")
        print("\nThis may or may not be an error depending on idempotency guards.")
        return True  # Not a hard failure
    else:
        print("✅ AUDIT PASSED - No duplicate table creations")
        return True

if __name__ == "__main__":
    import sys
    success = audit_tables()
    sys.exit(0 if success else 1)
