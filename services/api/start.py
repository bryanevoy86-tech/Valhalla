import os
import sys
import subprocess
import uvicorn

# Run migrations before starting the app
if __name__ == "__main__":
    # Check if we should skip migrations (for local dev or testing)
    skip_migrations = os.getenv("SKIP_MIGRATIONS", "0").lower() in {"1", "true", "yes"}
    
    if not skip_migrations:
        print("="*80)
        print("RUNNING DATABASE MIGRATIONS...")
        print("="*80)
        try:
            # Change to the workspace directory where alembic.ini is located
            workspace_root = "/app"  # In Docker
            if not os.path.exists(workspace_root):
                workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=workspace_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode != 0:
                print("="*80)
                print(f"❌ STARTUP FAILED: Migrations failed with code {result.returncode}")
                print("Core pipeline tables (leads, deals) require successful migration.")
                print("Please check database connection and alembic configuration.")
                print("="*80)
                sys.exit(1)
            else:
                print("✅ Migrations completed successfully")
        except subprocess.TimeoutExpired:
            print("="*80)
            print(f"❌ STARTUP FAILED: Migration timeout (60s exceeded)")
            print("="*80)
            sys.exit(1)
        except Exception as e:
            print("="*80)
            print(f"❌ STARTUP FAILED: Migration error: {e}")
            print("="*80)
            sys.exit(1)
        print("="*80)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "10000")),
        reload=False,
    )
