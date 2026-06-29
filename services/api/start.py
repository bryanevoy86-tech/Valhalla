import os
import uvicorn

"""
Web service startup script for Render.

This script now ONLY starts the Uvicorn web server.
Database migrations are run separately via Render's Pre-Deploy Command:
  python scripts/render_migrate.py

Architecture:
  Pre-Deploy Phase: python scripts/render_migrate.py (runs migrations)
  Web Service Phase: python start.py (starts Uvicorn immediately)

This separation ensures:
  - Migrations run and complete before web service starts
  - Web service opens port immediately (Render sees it as healthy)
  - No timeout waiting for migrations during web service startup
  - Clear separation of concerns
"""

if __name__ == "__main__":
    print("=" * 80)
    print("VALHALLA API - WEB SERVICE STARTUP")
    print("=" * 80)
    print()
    print("Note: Database migrations must be run separately via pre-deploy command:")
    print("  python scripts/render_migrate.py")
    print()
    
    # Get configuration
    port = int(os.getenv("PORT", "10000"))
    host = "0.0.0.0"
    
    print(f"🚀 Starting Uvicorn:")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   App: main:app")
    print()
    print("=" * 80)
    
    # Start the web server
    # This opens the port immediately and Render considers the service healthy
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,
    )
