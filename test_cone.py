#!/usr/bin/env python
"""Quick test just for cone router."""
try:
    print("Importing cone router...")
    from backend.app.core_gov.cone.router import router
    print("✅ Cone router imported successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
