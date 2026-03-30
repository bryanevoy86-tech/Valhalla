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
            # alembic.ini is in the workspace root, not in services/api
            # In Docker: /app/alembic.ini
            # Locally: ../../../alembic.ini (relative to services/api)
            workspace_root = "/app"
            if not os.path.exists(os.path.join(workspace_root, "alembic.ini")):
                # Fallback: try to find it relative to current script
                script_dir = os.path.dirname(os.path.abspath(__file__))
                workspace_root = os.path.dirname(os.path.dirname(script_dir))
            
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
                print(f"Workspace root: {workspace_root}")
                print(f"alembic.ini exists: {os.path.exists(os.path.join(workspace_root, 'alembic.ini'))}")
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
