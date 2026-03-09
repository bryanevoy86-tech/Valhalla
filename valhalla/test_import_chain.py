#!/usr/bin/env python
"""Debug import chain."""
import sys

print("1. Importing Request...")
from fastapi import Request
print("   OK")

print("2. Importing HTTPException...")
from fastapi import HTTPException
print("   OK")

print("3. Importing load_settings...")
from backend.app.core_gov.settings.config import load_settings
print("   OK")

print("4. Importing require_dev_key...")
from backend.app.core_gov.security.devkey.deps import require_dev_key
print("   OK")

print("5. Testing require_dev_key function...")
print(f"   Type: {type(require_dev_key)}")
print(f"   Callable: {callable(require_dev_key)}")
import inspect
print(f"   Signature: {inspect.signature(require_dev_key)}")

print("6. Creating Depends object...")
from fastapi import Depends
dep = Depends(require_dev_key)
print(f"   Type: {type(dep)}")

print("7. Trying to get signature of Depends.dependency...")
print(f"   dep.dependency: {dep.dependency}")
print(f"   Type of dep.dependency: {type(dep.dependency)}")
try:
    sig = inspect.signature(dep.dependency)
    print(f"   Signature: {sig}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n✅ Done")
