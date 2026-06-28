#!/usr/bin/env python
"""Database migration runner for Valhalla.

Handles Alembic migrations with fallback for multiple heads scenarios.
"""
import subprocess
import sys
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

def run_migrations() -> int:
    """Run Alembic migrations. Returns exit code 0 on success, non-zero on failure."""
    
    # This script is in services/api, so just use current directory
    app_root = Path.cwd()
    
    log.info("================================================================================")
    log.info("RUNNING DATABASE MIGRATIONS")
    log.info("================================================================================")
    log.info(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET').replace(':@', ':***@')}")
    log.info(f"Workspace root: {app_root}")
    
    # Attempt 1: Standard upgrade to head
    log.info("\n[Attempt 1] Running: alembic upgrade head")
    result = subprocess.run(
        ["python", "-m", "alembic", "upgrade", "head"],
        capture_output=False,
        text=True
    )
    
    if result.returncode == 0:
        log.info("✅ Migrations completed successfully")
        return 0
    
    # Attempt 2: If multiple heads, try upgrading to specific branch
    log.info("\n[Attempt 2] Multiple heads detected. Checking available heads...")
    heads_result = subprocess.run(
        ["python", "-m", "alembic", "heads"],
        capture_output=True,
        text=True
    )
    
    if heads_result.returncode == 0:
        heads_output = heads_result.stdout.strip()
        log.info(f"Available heads:\n{heads_output}")
        
        # Try to find the core_pipeline head
        lines = heads_output.split("\n")
        core_head = None
        for line in lines:
            if "core_pipeline" in line.lower():
                # Extract revision ID (first part before space)
                parts = line.split()
                if parts:
                    core_head = parts[0]
                    break
        
        if core_head:
            log.info(f"\n[Attempt 2] Upgrading to core_pipeline head: {core_head}")
            result = subprocess.run(
                ["python", "-m", "alembic", "upgrade", core_head],
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                log.info("✅ Migrations completed successfully (via core_pipeline branch)")
                return 0
    
    # Attempt 3: As last resort, current
    log.info("\n[Attempt 3] Attempting downgrade to current state...")
    result = subprocess.run(
        ["python", "-m", "alembic", "current"],
        capture_output=True,
        text=True
    )
    log.info(f"Current migration state:\n{result.stdout}")
    
    log.error("\n================================================================================")
    log.error("❌ STARTUP FAILED: Migrations failed with code 255")
    log.error("Core pipeline tables (leads, deals) require successful migration.")
    log.error(f"Workspace root: {app_root}")
    log.error("alembic.ini exists: " + str((app_root.parent / "alembic.ini").exists()))
    log.error("DATABASE_URL set: " + str("DATABASE_URL" in os.environ))
    log.error("Please check database connection and alembic configuration.")
    log.error("================================================================================")
    
    return 255


if __name__ == "__main__":
    exit_code = run_migrations()
    sys.exit(exit_code)
