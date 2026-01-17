#!/usr/bin/env python3
import os
import re

IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".converge_reports", "dist", "build"}

PATTERNS = {
    "Hardcoded localhost URL": re.compile(r"http://localhost:\d+|127\.0\.0\.1:\d+"),
    "Hardcoded port 3000/8000/5000": re.compile(r"listen\(\s*(3000|8000|5000)\s*\)|--port\s+(3000|8000|5000)"),
    "Missing process.env.PORT usage (Node)": re.compile(r"listen\("),
    "Health endpoints": re.compile(r"(/health|/api/health|/ping|/status)"),
    "CORS mentions": re.compile(r"\bcors\b", re.IGNORECASE),
    "ENV var access": re.compile(r"process\.env\.[A-Z0-9_]+|os\.environ\[['\"][A-Z0-9_]+['\"]\]|os\.getenv\(['\"][A-Z0-9_]+['\"]\)"),
}

NODE_FILES = (".js", ".ts", ".mjs", ".cjs")
PY_FILES = (".py",)

def walk_files(root="."):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        for fn in filenames:
            p = os.path.join(dirpath, fn)
            yield p

def read_text(path: str) -> str | None:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return None

def main():
    findings = {k: [] for k in PATTERNS.keys()}

    for p in walk_files("."):
        ext = os.path.splitext(p)[1].lower()
        if ext not in NODE_FILES + PY_FILES:
            continue
        txt = read_text(p)
        if not txt:
            continue

        for name, rgx in PATTERNS.items():
            if rgx.search(txt):
                findings[name].append(p)

    print("Render sanity scan (quick indicators):\n")

    # Render/PORT guidance
    print("1) PORT binding sanity:")
    port_hits = []
    for p in findings["Hardcoded port 3000/8000/5000"]:
        port_hits.append(p)
    if port_hits:
        print("  Potential hardcoded port usage found (Render needs $PORT):")
        for p in sorted(set(port_hits))[:50]:
            print(f"   - {p}")
    else:
        print("  No obvious hardcoded ports found (good).")

    print("\n2) localhost references (breaks production):")
    if findings["Hardcoded localhost URL"]:
        for p in sorted(set(findings["Hardcoded localhost URL"]))[:50]:
            print(f"   - {p}")
    else:
        print("  None found (good).")

    print("\n3) Health endpoint presence (should exist and be lightweight):")
    if findings["Health endpoints"]:
        for p in sorted(set(findings["Health endpoints"]))[:50]:
            print(f"   - {p}")
    else:
        print("  No obvious health route references found. Make sure /health exists.")

    print("\n4) CORS references (WeWeb -> Render needs correct CORS):")
    if findings["CORS mentions"]:
        for p in sorted(set(findings["CORS mentions"]))[:50]:
            print(f"   - {p}")
    else:
        print("  No obvious CORS config found. If WeWeb calls fail in-browser, add CORS.")

    print("\n5) ENV var usage (confirm these are set in Render service env):")
    if findings["ENV var access"]:
        for p in sorted(set(findings["ENV var access"]))[:50]:
            print(f"   - {p}")
    else:
        print("  No obvious env var usage found (unlikely for a backend).")

    print("\nNote: This is a heuristic scan. Final truth is always Render Logs at boot + first request.")

if __name__ == "__main__":
    main()
