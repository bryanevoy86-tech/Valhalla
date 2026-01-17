#!/usr/bin/env python3
import hashlib
import os
from collections import defaultdict

IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".converge_reports", "dist", "build"}
IGNORE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".pdf", ".mp4", ".mov", ".exe", ".dll"}

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def should_skip(path: str) -> bool:
    base = os.path.basename(path)
    if base.startswith(".") and base not in {".env.example"}:
        # allow most dotfiles to be skipped except examples
        return True
    _, ext = os.path.splitext(path)
    if ext.lower() in IGNORE_EXTS:
        return True
    return False

def walk_files(root="."):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            if should_skip(p):
                continue
            yield p

def main():
    hashes = defaultdict(list)
    for p in walk_files("."):
        try:
            digest = sha256_file(p)
            hashes[digest].append(p)
        except Exception:
            continue

    dup_groups = [paths for paths in hashes.values() if len(paths) > 1]
    dup_groups.sort(key=lambda g: (-len(g), g[0]))

    print("Exact duplicate files by SHA256 (same content):")
    if not dup_groups:
        print("  None found.")
        return

    for i, group in enumerate(dup_groups, 1):
        print(f"\n[{i}] {len(group)} duplicates:")
        for p in group:
            print(f"  - {p}")

if __name__ == "__main__":
    main()
