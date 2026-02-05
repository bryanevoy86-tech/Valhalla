"""Audit which routers/modules referenced in app.main are missing or failing imports.

Run:
  python tools/audit_missing_routers.py

Optional:
  MAIN_FILE=/path/to/main.py python tools/audit_missing_routers.py
"""

import os
import sys
import re
import importlib

# Add services/api to path so we can import app modules
sys.path.insert(0, "services/api")

MAIN_FILE = os.getenv("MAIN_FILE", "valhalla/services/api/app/main.py")

IMPORT_PATTERNS = [
    r"from\s+(app\.routers(?:\.[\w_]+)?)\s+import\s+([\w_,\s]+)",
    r"from\s+(app\.routes(?:\.[\w_]+)?)\s+import\s+([\w_,\s]+)",
    r"from\s+(app\.core\.prelaunch\.[\w_\.]+)\s+import\s+router\s+as\s+[\w_]+",
    r"from\s+(app\.core\.prelaunch\.[\w_\.]+)\s+import\s+router",
]

def read_main_source() -> str:
    if not os.path.exists(MAIN_FILE):
        raise RuntimeError(f"Cannot locate file: {MAIN_FILE}")
    with open(MAIN_FILE, "r", encoding="utf-8") as f:
        return f.read()

def normalize_names(raw: str):
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p and not p.startswith("#")]

def try_import(module: str, name: str | None = None):
    try:
        m = importlib.import_module(module)
        if name:
            getattr(m, name)
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def main():
    src = read_main_source()

    found = []
    for pat in IMPORT_PATTERNS:
        for m in re.finditer(pat, src):
            base = m.group(1)
            names = m.group(2) if m.lastindex and m.lastindex >= 2 else ""
            if names:
                for n in normalize_names(names):
                    found.append((base, n))
            else:
                found.append((base, None))

    # Dedup
    uniq = []
    seen = set()
    for item in found:
        if item in seen:
            continue
        seen.add(item)
        uniq.append(item)

    ok, bad = [], []
    for base, name in uniq:
        if name is None:
            success, err = try_import(base)
            (ok if success else bad).append((base, name, err))
        else:
            success, err = try_import(base, name)
            (ok if success else bad).append((base, name, err))

    print("\n=== IMPORT OK ===")
    for base, name, _ in ok:
        print(f"  OK: {base}" + (f".{name}" if name else ""))

    print("\n=== MISSING / FAILING ===")
    for base, name, err in bad:
        print(f"  FAIL: {base}" + (f".{name}" if name else "") + (f" -> {err}" if err else ""))

    print("\n=== SUMMARY ===")
    print(f"  OK:   {len(ok)}")
    print(f"  FAIL: {len(bad)}")

if __name__ == "__main__":
    main()
