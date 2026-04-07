import os
import subprocess
import sys

def run():
    # Add workspace root to Python path if needed
    script_dir = os.path.dirname(os.path.abspath(__file__))  # services/api
    workspace_root = os.path.dirname(os.path.dirname(script_dir))  # d:\dev
    
    if workspace_root not in sys.path:
        sys.path.insert(0, workspace_root)
    
    os.environ.setdefault("APP_ENV", "production")
    os.environ.setdefault("VALHALLA_LAUNCH_MODE", "launch_core")

    print("=" * 80)
    print("VALHALLA LAUNCH CORE STARTUP")
    print("=" * 80)

    try:
        print("Running alembic upgrade head...")
        subprocess.run(["alembic", "upgrade", "head"], check=True, cwd=workspace_root)
        print("Alembic upgrade complete.")
    except Exception as e:
        print(f"WARNING: Alembic upgrade failed or skipped: {e}")

    try:
        import uvicorn
        # Import the app directly so it's in the current namespace
        from services.api.main_launch import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("PORT", "8000")),
            reload=False,
        )
    except Exception as e:
        print(f"FATAL: Launch core startup failed: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run()
