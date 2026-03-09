#!/usr/bin/env python
"""Test PACK E routers import."""
try:
    from backend.app.core_gov.cone.router import router as cone_router
    from backend.app.core_gov.capital.router import router as capital_router
    from backend.app.core_gov.config.router import router as config_router
    from backend.app.core_gov.notify.router import router as notify_router
    from backend.app.core_gov.jobs.router import router as jobs_router
    print("✅ All 5 routers imported successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
