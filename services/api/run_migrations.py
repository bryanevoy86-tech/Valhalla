#!/usr/bin/env python
"""Database migration runner for Valhalla.

Handles Alembic migrations with fallback for multiple heads scenarios.
Uses absolute paths to root Alembic config for clarity and reliability.
"""
import subprocess
import sys
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

def find_repo_root() -> Path:
    """Find repo root by looking for alembic.ini from current directory."""
    current = Path.cwd()
    
    # If we're in services/api, root is parent/parent
    if current.name == "api" and (current.parent.name == "services"):
        return current.parent.parent
    
    # If we're at repo root already
    if (current / "alembic.ini").exists():
        return current
    
    # Try parent
    if (current.parent / "alembic.ini").exists():
        return current.parent
    
    # Try grandparent
    if (current.parent.parent / "alembic.ini").exists():
        return current.parent.parent
    
    # Fallback to /app (Render environment)
    if Path("/app/alembic.ini").exists():
        return Path("/app")
    
    raise FileNotFoundError("Could not find repository root with alembic.ini")

def run_migrations() -> int:
    """Run Alembic migrations using absolute paths. Returns exit code 0 on success, non-zero on failure."""
    
    try:
        repo_root = find_repo_root()
    except FileNotFoundError as e:
        log.error(f"❌ {e}")
        return 1
    
    alembic_ini = repo_root / "alembic.ini"
    alembic_dir = repo_root / "alembic"
    versions_dir = alembic_dir / "versions"
    
    log.info("================================================================================")
    log.info("RUNNING DATABASE MIGRATIONS")
    log.info("================================================================================")
    log.info(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'NOT SET').replace(':@', ':***@')}")
    log.info(f"Repository root: {repo_root}")
    log.info(f"Alembic config: {alembic_ini} (exists: {alembic_ini.exists()})")
    log.info(f"Alembic scripts: {alembic_dir} (exists: {alembic_dir.exists()})")
    log.info(f"Versions folder: {versions_dir} (exists: {versions_dir.exists()})")
    log.info(f"Current working directory: {Path.cwd()}")
    
    # Validate prerequisites
    if not alembic_ini.exists():
        log.error(f"❌ Alembic config not found: {alembic_ini}")
        return 1
    
    if not alembic_dir.exists():
        log.error(f"❌ Alembic scripts folder not found: {alembic_dir}")
        return 1
    
    if not versions_dir.exists():
        log.error(f"❌ Alembic versions folder not found: {versions_dir}")
        return 1
    
    # Attempt 1: Standard upgrade to head with explicit config
    log.info(f"\n[Attempt 1] Running: python -m alembic -c {alembic_ini} upgrade head")
    result = subprocess.run(
        ["python", "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
        capture_output=False,
        text=True
    )
    
    if result.returncode == 0:
        log.info("✅ Migrations completed successfully")
        return 0
    
    # Attempt 2: If multiple heads, try upgrading to specific branch
    log.info(f"\n[Attempt 2] Multiple heads detected. Checking available heads...")
    heads_result = subprocess.run(
        ["python", "-m", "alembic", "-c", str(alembic_ini), "heads"],
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
                ["python", "-m", "alembic", "-c", str(alembic_ini), "upgrade", core_head],
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                log.info("✅ Migrations completed successfully (via core_pipeline branch)")
                return 0
    
    # Attempt 3: As last resort, show current state
    log.info(f"\n[Attempt 3] Checking current migration state...")
    result = subprocess.run(
        ["python", "-m", "alembic", "-c", str(alembic_ini), "current"],
        capture_output=True,
        text=True
    )
    log.info(f"Current migration state:\n{result.stdout}")
    
    log.error("\n================================================================================")
    log.error("❌ STARTUP FAILED: Migrations failed with code 255")
    log.error("Core pipeline tables (leads, deals) require successful migration.")
    log.error(f"Repository root: {repo_root}")
    log.error(f"Alembic config: {alembic_ini} (exists: {alembic_ini.exists()})")
    log.error(f"Alembic scripts: {alembic_dir} (exists: {alembic_dir.exists()})")
    log.error(f"DATABASE_URL set: {os.getenv('DATABASE_URL') is not None}")
    log.error("Please check database connection and alembic configuration.")
    log.error("================================================================================")
    
    return 255


if __name__ == "__main__":
    exit_code = run_migrations()
    sys.exit(exit_code)
