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
        
        # Debug: Print database URL (redacted for security)
        db_url = os.getenv("DATABASE_URL", "").replace(":", ":*****@", 1) if os.getenv("DATABASE_URL") else "[NOT SET]"
        print(f"DATABASE_URL: {db_url}")
        
        try:
            # alembic.ini is in the workspace root (/app in Docker, parent dirs locally)
            # Start from current dir and traverse up until we find alembic.ini
            current_dir = os.path.abspath(".")
            workspace_root = None
            
            # First check Docker path with alembic folder (not just alembic.ini)
            if os.path.exists("/app/alembic") and os.path.isdir("/app/alembic"):
                workspace_root = "/app"
            # Then check common Docker path with just alembic.ini
            elif os.path.exists("/app/alembic.ini"):
                workspace_root = "/app"
            else:
                # Search up from current directory
                search_dir = current_dir
                for _ in range(5):  # Search up to 5 levels
                    alembic_ini = os.path.join(search_dir, "alembic.ini")
                    alembic_dir = os.path.join(search_dir, "alembic")
                    # Prefer if we find both alembic.ini AND alembic folder
                    if os.path.exists(alembic_ini) and os.path.isdir(alembic_dir):
                        workspace_root = search_dir
                        break
                    # Otherwise accept just alembic.ini as fallback
                    elif os.path.exists(alembic_ini):
                        workspace_root = search_dir
                        break
                    search_dir = os.path.dirname(search_dir)
            
            if not workspace_root:
                raise RuntimeError(f"Could not find alembic.ini starting from {current_dir}")
            
            print(f"Workspace root: {workspace_root}")
            
            # Explicitly pass current environment to subprocess  
            env = os.environ.copy()
            
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=workspace_root,
                capture_output=True,
                text=True,
                timeout=60,
                env=env  # Explicitly pass environment
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
                print(f"DATABASE_URL set: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")
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
