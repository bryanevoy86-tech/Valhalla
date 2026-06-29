import os
import sys
import subprocess
import uvicorn

"""
Web service startup script for Render.

This script:
1. Optionally runs the owner password reset (if RESET_OWNER_PASSWORD=true)
2. Starts the Uvicorn web server

Database migrations are run separately via Render's Pre-Deploy Command:
  python scripts/render_migrate.py

Architecture:
  Pre-Deploy Phase: python scripts/render_migrate.py (runs migrations)
  Pre-Startup Phase (optional): python scripts/reset_owner_password.py (resets admin)
  Web Service Phase: python start.py (starts Uvicorn immediately)

This separation ensures:
  - Migrations run and complete before web service starts
  - Admin password reset runs once if needed
  - Web service opens port immediately (Render sees it as healthy)
  - No timeout waiting for migrations during web service startup
  - Clear separation of concerns
"""

def run_optional_reset():
    """Run password reset script if RESET_OWNER_PASSWORD=true."""
    reset_enabled = (os.getenv("RESET_OWNER_PASSWORD") or "").strip().lower()
    if reset_enabled not in {"true", "1", "yes", "on"}:
        return
    
    print("\n" + "=" * 80)
    print("OPTIONAL: Running owner password reset...")
    print("=" * 80 + "\n")
    
    reset_script = "/app/scripts/reset_owner_password.py"
    
    # Check if script exists
    if not os.path.exists(reset_script):
        print(f"⚠️  Reset script not found at {reset_script}, skipping")
        return
    
    try:
        result = subprocess.run(
            [sys.executable, reset_script],
            capture_output=True,
            text=True,
            timeout=60,
        )
        
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print("✅ Password reset completed successfully\n")
        else:
            print(f"⚠️  Password reset exited with code {result.returncode}\n")
            
    except subprocess.TimeoutExpired:
        print("⚠️  Password reset timed out (> 60s)\n")
    except Exception as e:
        print(f"⚠️  Error running password reset: {e}\n")


if __name__ == "__main__":
    print("=" * 80)
    print("VALHALLA API - WEB SERVICE STARTUP")
    print("=" * 80)
    print()
    print("Note: Database migrations must be run separately via pre-deploy command:")
    print("  python scripts/render_migrate.py")
    print()
    
    # Optionally run password reset
    run_optional_reset()
    
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
