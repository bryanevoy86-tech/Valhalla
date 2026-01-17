"""
Simple migration runner endpoint to create research tables.
This can be called via the API to run migrations without shell access.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
import subprocess
import os
from app.metrics.service import MetricsService
from app.metrics.schemas import MetricsOut

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_key(x_admin_key: str = None):
    """Require admin key for sensitive operations"""
    expected = os.getenv("HEIMDALL_BUILDER_API_KEY", "")
    if not expected or x_admin_key != expected:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return True


@router.post("/migrate")
def run_migrations(_: bool = Depends(require_admin_key)):
    """
    Run Alembic migrations to create/update database tables.
    Requires X-Admin-Key header with HEIMDALL_BUILDER_API_KEY value.
    """
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/db/check")
def check_database(_: bool = Depends(require_admin_key)):
    """
    Check if research tables exist in the database.
    Requires X-Admin-Key header.
    """
    from app.core.db import SessionLocal
    
    db = SessionLocal()
    try:
        # Check for research tables
        result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('research_sources', 'research_docs', 'research_queries', 'playbooks')
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
        
        # Check alembic version
        version_result = db.execute(text("SELECT version_num FROM alembic_version"))
        version = version_result.scalar()
        
        return {
            "ok": True,
            "research_tables_exist": tables,
            "research_tables_count": len(tables),
            "expected_tables": 4,
            "all_tables_exist": len(tables) == 4,
            "alembic_version": version
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        db.close()


@router.get("/metrics", response_model=MetricsOut)
def get_admin_metrics():
    """Return runtime metrics counters for admin overview."""
    return MetricsService.get_metrics()
