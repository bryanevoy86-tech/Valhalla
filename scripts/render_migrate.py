#!/usr/bin/env python
"""
Dedicated migration runner for Render pre-deploy command.

This script is meant to run as a Render pre-deploy command, separate from the web service.
It runs database migrations and exits with a clear status code.

Usage:
  python scripts/render_migrate.py

On Render, use as Pre-Deploy Command:
  python scripts/render_migrate.py
"""

import os
import sys
import subprocess
import time

def find_alembic_config():
    """Find alembic.ini in Docker or local environment."""
    # Check Docker path first
    if os.path.exists("/app/alembic.ini"):
        return "/app", "/app/alembic.ini"
    
    # Check local/dev path
    current_dir = os.path.abspath(".")
    for _ in range(5):
        alembic_ini = os.path.join(current_dir, "alembic.ini")
        if os.path.exists(alembic_ini):
            return current_dir, alembic_ini
        current_dir = os.path.dirname(current_dir)
    
    raise RuntimeError("Could not find alembic.ini in /app or parent directories")

def mask_database_url(url):
    """Mask sensitive database URL for logging."""
    if not url:
        return "[NOT SET]"
    if "://" in url:
        scheme, rest = url.split("://", 1)
        if "@" in rest:
            creds, host = rest.rsplit("@", 1)
            return f"{scheme}://***:***@{host}"
        return url
    return url

def run_migrations():
    """Run database migrations."""
    print("=" * 80)
    print("RENDER PRE-DEPLOY MIGRATION RUNNER")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # Find configuration
        workspace_root, alembic_ini_path = find_alembic_config()
        
        # Check environment
        db_url = os.getenv("DATABASE_URL", "")
        masked_url = mask_database_url(db_url)
        
        # Print diagnostics
        print(f"Workspace root: {workspace_root}")
        print(f"Alembic config: {alembic_ini_path}")
        print(f"Alembic folder exists: {os.path.isdir(os.path.join(workspace_root, 'alembic'))}")
        print(f"DATABASE_URL: {masked_url}")
        print(f"Running from: {workspace_root}")
        print()
        
        # Check that database is configured
        if not db_url:
            print("❌ ERROR: DATABASE_URL environment variable not set")
            print("   Migration cannot proceed without database connection")
            return False
        
        # Get current state
        print("🔍 Checking current migration state...")
        heads_result = subprocess.run(
            ["python", "-m", "alembic", "-c", alembic_ini_path, "heads"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        heads_count = len([h for h in heads_result.stdout.strip().split('\n') if h.strip()])
        current_result = subprocess.run(
            ["python", "-m", "alembic", "-c", alembic_ini_path, "current"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(f"  Current head count: {heads_count}")
        if current_result.stdout.strip():
            print(f"  Current revision: {current_result.stdout.strip()}")
        print()
        
        # Run migrations
        print("🚀 Running migrations: python -m alembic -c <config> upgrade head")
        print()
        
        result = subprocess.run(
            ["python", "-m", "alembic", "-c", alembic_ini_path, "upgrade", "head"],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes max
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr and result.returncode != 0:
            print("STDERR:")
            print(result.stderr)
        
        elapsed = time.time() - start_time
        
        print()
        print("=" * 80)
        
        if result.returncode == 0:
            print(f"✅ MIGRATIONS COMPLETED SUCCESSFULLY (elapsed: {elapsed:.1f}s)")
            print("=" * 80)
            return True
        else:
            print(f"❌ MIGRATIONS FAILED (returncode={result.returncode}, elapsed: {elapsed:.1f}s)")
            print("=" * 80)
            return False
            
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print("=" * 80)
        print(f"❌ MIGRATIONS TIMED OUT (exceeded 1800s limit, elapsed: {elapsed:.1f}s)")
        print("   Check database connection and query logs for blocked migrations")
        print("=" * 80)
        return False
    
    except Exception as e:
        elapsed = time.time() - start_time
        print("=" * 80)
        print(f"❌ MIGRATION ERROR (elapsed: {elapsed:.1f}s)")
        print(f"   {e}")
        print("=" * 80)
        return False

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
