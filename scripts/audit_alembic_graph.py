#!/usr/bin/env python
"""Audit Alembic migration graph for structural issues."""

import os
import re
from collections import defaultdict
from pathlib import Path

def extract_migration_info(file_path):
    """Extract revision, down_revision, and branch_labels from a migration file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Extract revision (handles both old and new Alembic formats)
    # Old: revision = 'abc'
    # New: revision: str = 'abc'
    rev_match = re.search(r"^revision\s*(?::\s*[\w\[\],\s.]+)?\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE)
    revision = rev_match.group(1) if rev_match else None
    
    # Extract down_revision (handles both old and new formats)
    # Old: down_revision = 'abc' or down_revision = ('a', 'b')
    # New: down_revision: Union[str, ...] = 'abc' or down_revision: Union[...] = ('a', 'b')
    down_match = re.search(r"^down_revision\s*(?::\s*[^=]+)?\s*=\s*(.+?)$", content, re.MULTILINE)
    down_revision = None
    if down_match:
        down_str = down_match.group(1).strip()
        # Handle various formats: 'abc', None, ('a', 'b'), [...]
        if down_str.lower() == 'none':
            down_revision = None
        elif down_str.startswith("(") or down_str.startswith("["):
            # Extract multiple revisions
            parts = re.findall(r"['\"]([^'\"]+)['\"]", down_str)
            down_revision = parts
        elif down_str.startswith("'") or down_str.startswith('"'):
            down_str = re.search(r"['\"]([^'\"]+)['\"]", down_str)
            if down_str:
                down_revision = [down_str.group(1)]
    
    return revision, down_revision

def audit_graph():
    """Audit the alembic graph."""
    versions_dir = Path("alembic/versions")
    
    if not versions_dir.exists():
        print("❌ alembic/versions directory does not exist")
        return False
    
    files = sorted(versions_dir.glob("*.py"))
    files = [f for f in files if f.name != "__init__.py"]
    
    print(f"📊 Found {len(files)} migration files\n")
    
    revisions_to_files = defaultdict(list)
    down_revisions = defaultdict(list)
    base_migrations = []
    issues = []
    
    # Parse all files
    for file_path in files:
        revision, down_revision = extract_migration_info(file_path)
        
        if not revision:
            issues.append(f"❌ No revision found in {file_path.name}")
            continue
        
        revisions_to_files[revision].append(file_path.name)
        
        if down_revision is None:
            base_migrations.append((revision, file_path.name))
        elif isinstance(down_revision, list):
            for down_rev in down_revision:
                down_revisions[down_rev].append((revision, file_path.name))
        else:
            down_revisions[down_revision[0]].append((revision, file_path.name))
    
    # Check for duplicates
    print("🔍 Checking for duplicate revision IDs:")
    duplicates = {rev: files for rev, files in revisions_to_files.items() if len(files) > 1}
    if duplicates:
        for rev, file_list in duplicates.items():
            issues.append(f"❌ DUPLICATE: Revision '{rev}' in files: {', '.join(file_list)}")
            print(f"  ❌ DUPLICATE: Revision '{rev}'")
            for f in file_list:
                print(f"     - {f}")
    else:
        print("  ✅ No duplicate revision IDs found\n")
    
    # Check for missing down_revisions
    print("🔍 Checking for missing down_revision targets:")
    missing_downs = {}
    for down_rev, upstreams in down_revisions.items():
        if down_rev not in revisions_to_files:
            missing_downs[down_rev] = upstreams
    
    if missing_downs:
        for down_rev, upstreams in missing_downs.items():
            issues.append(f"❌ MISSING: down_revision '{down_rev}' referenced but no file creates it")
            print(f"  ❌ MISSING: down_revision '{down_rev}'")
            for up_rev, up_file in upstreams:
                print(f"     - Referenced by: {up_file} (rev: {up_rev})")
    else:
        print("  ✅ All down_revisions point to existing migrations\n")
    
    # Report base migrations
    print(f"📍 Base migrations (down_revision = None):")
    if base_migrations:
        for rev, filename in base_migrations:
            print(f"  - {filename} (rev: {rev})")
    else:
        print("  ℹ️ No base migrations found")
    print()
    
    # Try to find heads using Alembic
    print("🔍 Checking Alembic heads:")
    try:
        import subprocess
        result = subprocess.run(
            ["python", "-m", "alembic", "-c", "alembic.ini", "heads"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            heads = result.stdout.strip().split('\n') if result.stdout.strip() else []
            print(f"  Found {len(heads)} head(s):")
            for head in heads:
                if head.strip():
                    print(f"    - {head.strip()}")
        else:
            print(f"  ⚠️ Alembic heads command failed:")
            if "Can't locate revision" in result.stderr:
                issues.append(f"❌ Alembic error: {result.stderr[:200]}")
                print(f"     {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        issues.append("❌ Alembic heads command timed out")
        print("  ❌ Alembic heads command timed out")
    except Exception as e:
        issues.append(f"❌ Error running Alembic: {e}")
        print(f"  ⚠️ Error: {e}")
    print()
    
    # Summary
    print("=" * 60)
    if issues:
        print(f"❌ AUDIT FAILED - {len(issues)} issue(s) found:\n")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("✅ AUDIT PASSED - Migration graph appears clean")
        return True

if __name__ == "__main__":
    import sys
    success = audit_graph()
    sys.exit(0 if success else 1)
