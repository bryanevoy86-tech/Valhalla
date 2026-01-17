from __future__ import annotations
import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SUSPECT_PATTERNS = [
    "SECRET_KEY",
    "VALHALLA_JWT_SECRET",
    "api_key",
    "apikey",
    "token=",
    "password",
    "passwd",
    "Authorization:",
    "BEGIN PRIVATE KEY",
]

IGNORE_DIRS = {".git", ".venv", "node_modules", "__pycache__", "dist", "build", ".pytest_cache"}

def iter_files(root: Path):
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}:
            continue
        if p.stat().st_size > 2_000_000:
            continue
        yield p

def scan_for_secrets() -> list[tuple[str, str]]:
    hits = []
    for p in iter_files(ROOT):
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for pat in SUSPECT_PATTERNS:
            if pat.lower() in text.lower():
                hits.append((str(p.relative_to(ROOT)), pat))
    return hits

def check_env_files():
    bad = []
    for name in [".env", ".env.sandbox", ".env.prod", ".env.local"]:
        p = ROOT / name
        if p.exists():
            bad.append(str(p))
    return bad

def check_caps_config():
    p = ROOT / "config" / "caps_limits.json"
    if not p.exists():
        return False, "Missing config/caps_limits.json"
    try:
        json.loads(p.read_text())
        return True, "caps_limits.json OK"
    except Exception as e:
        return False, f"caps_limits.json invalid JSON: {e}"

def main():
    print("VALHALLA SMOKE CHECK (cold-zone)")
    envs = check_env_files()
    if envs:
        print("\n[WARN] Found env files in repo root (ensure .gitignore protects them):")
        for e in envs:
            print(" -", e)

    ok, msg = check_caps_config()
    print("\n[INFO]", msg)

    hits = scan_for_secrets()
    if hits:
        print("\n[FAIL] Potential secrets/sensitive strings found:")
        for f, pat in hits[:50]:
            print(f" - {f}  (matched: {pat})")
        print("\nFix: remove/rotate secrets, move to env vars, ensure not logged/committed.")
        sys.exit(1)

    print("\n[PASS] No obvious secret patterns detected (basic scan).")
    sys.exit(0)

if __name__ == "__main__":
    main()
