#!/usr/bin/env python3
"""
Audit Alembic migration graph for cycles, duplicates, and missing links.

Usage:
  python tools/audit_alembic_graph.py services/api/alembic/versions

This will:
  - Detect true cycles (not just multiple heads)
  - Find duplicate revision IDs
  - Find missing referenced down_revisions
  - List all heads
  - Report exact problem locations
"""

import os
import re
import sys
from collections import defaultdict, deque

VERSIONS_DIR = sys.argv[1] if len(sys.argv) > 1 else "services/api/alembic/versions"

REV_RE = re.compile(r"^\s*revision\s*(?::\s*str)?\s*=\s*['\"]([^'\"]+)['\"]\s*$", re.MULTILINE)
DOWN_RE = re.compile(r"^\s*down_revision\s*(?::[^=]*)?\s*=\s*(.+?)\s*$", re.MULTILINE)


def parse_down_revision(raw: str):
    """Parse down_revision value - can be None, single string, or tuple of strings."""
    raw = raw.strip()
    if raw == "None":
        return []
    # Handles: 'abc', ("a","b"), ('a', 'b')
    if raw.startswith(("(", "[")):
        ids = re.findall(r"['\"]([^'\"]+)['\"]", raw)
        return ids
    m = re.search(r"['\"]([^'\"]+)['\"]", raw)
    return [m.group(1)] if m else []


def read_revision_file(path: str):
    """Parse a migration file and return (revision_id, [down_revision_ids])."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            txt = f.read()
    except Exception as e:
        print(f"ERROR reading {path}: {e}", file=sys.stderr)
        return None, []

    rev_m = REV_RE.search(txt)
    if not rev_m:
        return None, []

    revision = rev_m.group(1).strip()
    down_m = DOWN_RE.search(txt)
    downs = parse_down_revision(down_m.group(1)) if down_m else []
    return revision, downs


def main():
    """Main audit logic."""
    if not os.path.isdir(VERSIONS_DIR):
        print(f"ERROR: Directory not found: {VERSIONS_DIR}", file=sys.stderr)
        sys.exit(1)

    files = []
    for root, _, fnames in os.walk(VERSIONS_DIR):
        for fn in fnames:
            if fn.endswith(".py") and not fn.startswith("__"):
                files.append(os.path.join(root, fn))

    print(f"\n{'='*60}")
    print(f"ALEMBIC MIGRATION GRAPH AUDIT")
    print(f"{'='*60}")
    print(f"Versions directory: {VERSIONS_DIR}")
    print(f"Migration files found: {len(files)}\n")

    rev_to_file = {}
    graph = defaultdict(list)
    indeg = defaultdict(int)
    duplicates = []
    unknown_downs = []

    # Parse all files
    for fp in sorted(files):
        rev, downs = read_revision_file(fp)
        if not rev:
            continue

        filename = os.path.basename(fp)

        # Check for duplicates
        if rev in rev_to_file:
            duplicates.append((rev, rev_to_file[rev], fp))
            print(f"⚠️  DUPLICATE revision ID: {rev}")
            print(f"    File 1: {rev_to_file[rev]}")
            print(f"    File 2: {fp}\n")

        rev_to_file[rev] = fp

        if rev not in indeg:
            indeg[rev] = 0

        # Build graph: edge from down_rev -> rev (up the chain)
        for d in downs:
            graph[d].append(rev)
            indeg[rev] += 1

    # Find unknown down_revisions
    print("Checking for unknown down_revision references...\n")
    for fp in sorted(files):
        rev, downs = read_revision_file(fp)
        if not rev:
            continue

        filename = os.path.basename(fp)
        for d in downs:
            if d not in rev_to_file and d != "None":
                unknown_downs.append((rev, d, fp))
                print(f"⚠️  MISSING down_revision: {d}")
                print(f"    Referenced by: {rev} ({filename})")
                print(f"    File: {fp}\n")

    # Topological sort to detect cycles (Kahn's algorithm)
    print("Running topological sort to detect cycles...\n")
    q = deque([r for r, deg in indeg.items() if deg == 0])
    visited = 0
    order = []

    while q:
        n = q.popleft()
        order.append(n)
        visited += 1
        for nxt in graph.get(n, []):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)

    # Revisions that couldn't be visited = in a cycle
    cyclic = sorted([r for r, deg in indeg.items() if deg > 0])

    # Report findings
    print(f"{'='*60}")
    print("AUDIT RESULTS")
    print(f"{'='*60}\n")

    if duplicates:
        print(f"❌ FOUND {len(duplicates)} DUPLICATE REVISION IDs:")
        for rev, a, b in duplicates:
            print(f"   {rev}")
            print(f"     - {os.path.basename(a)}")
            print(f"     - {os.path.basename(b)}")
        print()

    if unknown_downs:
        print(f"❌ FOUND {len(unknown_downs)} MISSING DOWN_REVISION REFERENCES:")
        for rev, d, fp in unknown_downs:
            print(f"   {rev} -> missing {d}")
            print(f"     in {os.path.basename(fp)}")
        print()

    if cyclic:
        print(f"❌ CYCLE DETECTED - {len(cyclic)} revisions in cycle(s):")
        for r in cyclic:
            filename = os.path.basename(rev_to_file.get(r, "UNKNOWN"))
            print(f"   {r}")
            print(f"     ({filename})")
        print()
        print("ACTION: These revisions have circular dependencies.")
        print("        Inspect their down_revision values and fix the loop(s).")
        return 2

    # Find heads (revisions that have no outgoing edges in the graph)
    # These are revisions never referenced as a down_revision
    referenced_as_down = set()
    for fp in files:
        rev, downs = read_revision_file(fp)
        if not rev:
            continue
        for d in downs:
            referenced_as_down.add(d)

    heads = sorted([r for r in rev_to_file.keys() if r not in referenced_as_down])

    print(f"✅ NO CYCLES DETECTED")
    print(f"   Total revisions: {len(rev_to_file)}")
    print(f"   Topologically sorted: {len(order)} (should equal total)")
    print()
    print(f"   Heads (branch tips - not referenced as down_revision):")
    print(f"   Count: {len(heads)}\n")

    for head in heads[:30]:
        filename = os.path.basename(rev_to_file[head])
        print(f"   - {head}")
        print(f"     ({filename})")

    if len(heads) > 30:
        print(f"   ... and {len(heads) - 30} more")

    print()

    if len(heads) > 1:
        print(f"   ⚠️  MULTIPLE HEADS DETECTED ({len(heads)})")
        print(f"   This is normal for branching.")
        print(f"   Solution: Create merge migration(s) to consolidate into single head.")
    else:
        print(f"   ✅ Single head - clean linear chain")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
