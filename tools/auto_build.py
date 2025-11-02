"""
Heimdall auto-builder runner.
Uses the Builder API to automatically draft and apply code changes.

This script demonstrates how Heimdall can use the Builder API to:
1. Register as an agent
2. Create tasks
3. Upload code drafts
4. Apply changes (with optional dry-run first)

Usage:
    API_BASE=http://localhost:4000 BUILDER_KEY=test123 python tools/auto_build.py
"""

import os
import json
import sys
import time
import requests

API = os.getenv("API_BASE", "http://localhost:4000")
KEY = os.getenv("BUILDER_KEY", "test123")

HEADERS = {"X-API-Key": KEY, "Content-Type": "application/json"}


def post(path, data):
    """POST request with error handling"""
    r = requests.post(API + path, headers=HEADERS, data=json.dumps(data), timeout=30)
    if r.status_code >= 400:
        raise SystemExit(f"POST {path} failed {r.status_code}: {r.text}")
    return r.json()


def get(path):
    """GET request with error handling"""
    r = requests.get(API + path, headers=HEADERS, timeout=30)
    if r.status_code >= 400:
        raise SystemExit(f"GET {path} failed {r.status_code}: {r.text}")
    return r.json()


def ensure_registered():
    """Register Heimdall as a builder agent"""
    try:
        post("/builder/register", {"agent_name": "heimdall-bot", "version": "1.0"})
        print("✓ Registered as heimdall-bot")
    except SystemExit:
        pass  # Already registered


def create_task(title, scope, plan="auto-build"):
    """Create a new builder task"""
    result = post("/builder/tasks", {"title": title, "scope": scope, "plan": plan})
    task_id = result.get("task_id") or result.get("taskId")
    print(f"✓ Created task #{task_id}: {title}")
    return task_id


def upload_draft(task_id, files):
    """
    Upload draft files for a task.
    files = [{"path": "...", "mode": "add|replace", "content": "..."}]
    """
    result = post(f"/builder/draft?task_id={task_id}", files)
    print(f"✓ Uploaded {len(files)} file(s) for task #{task_id}")
    return result


def apply_changes(task_id, approve):
    """Apply changes (approve=True) or dry-run (approve=False)"""
    result = post("/builder/apply", {"task_id": task_id, "approve": approve})
    action = "Applied" if approve else "Dry-run"
    print(f"✓ {action} task #{task_id}")
    return result


# --- File templates ---

REPORTS_PY_CONTENT = '''"""
Reports router for summary metrics and analytics.
Provides read-only endpoints for monitoring research system health.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.db import get_db
from ..models.research import ResearchSource, ResearchDoc

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    """
    Get summary statistics for the research system.
    
    Returns:
        - sources: Total number of research sources
        - docs: Total number of research documents
        - embedded: Number of documents with embeddings
        - embedding_coverage: Percentage of docs with embeddings (0.0-1.0)
    """
    sources = db.query(ResearchSource).count()
    docs = db.query(ResearchDoc).count()
    embedded = db.query(ResearchDoc).filter(ResearchDoc.embedding_json.isnot(None)).count()
    coverage = (embedded / docs) if docs else 0.0
    
    return {
        "ok": True,
        "sources": sources,
        "docs": docs,
        "embedded": embedded,
        "embedding_coverage": round(coverage, 4)
    }
'''

TEST_REPORTS_CONTENT = '''"""
Smoke tests for reports endpoints.
"""

import os
import httpx

API = os.getenv("API_BASE", "http://localhost:4000")


def test_reports_summary():
    """Test the reports summary endpoint returns expected structure"""
    r = httpx.get(f"{API}/reports/summary", timeout=10)
    assert r.status_code == 200
    
    j = r.json()
    assert j.get("ok") is True
    assert "sources" in j
    assert "docs" in j
    assert "embedded" in j
'''


def load_file(path):
    """Load file content, return empty string if not found"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def synthesize_main_content():
    """
    Load main.py and ensure reports router is imported/included.
    Returns the updated content.
    """
    path = "services/api/main.py"
    current = load_file(path)
    
    if not current:
        raise SystemExit(f"Could not load {path}")
    
    # Check if already present
    has_import = "from app.routers.reports import router as reports_router" in current
    has_include = "app.include_router(reports_router" in current
    
    if has_import and has_include:
        print("  ℹ Reports router already wired in main.py")
        return current
    
    # Need to add - append at end
    additions = "\n# AUTO-INCLUDE: reports router\n"
    if not has_import:
        additions += "from app.routers.reports import router as reports_router\n"
    if not has_include:
        additions += "app.include_router(reports_router, prefix=\"/api\")\n"
    
    return current.rstrip() + "\n" + additions + "\n"


def build_reports():
    """Main auto-build function for reports feature"""
    print("\n🤖 Heimdall Auto-Builder: Reports Feature")
    print("=" * 50)
    
    ensure_registered()
    
    task_id = create_task(
        "Add /reports/summary endpoint",
        "services/api/app/routers/reports.py"
    )
    
    files = [
        {
            "path": "services/api/app/routers/reports.py",
            "mode": "replace",
            "content": REPORTS_PY_CONTENT
        },
        {
            "path": "services/api/main.py",
            "mode": "replace",
            "content": synthesize_main_content()
        },
        {
            "path": "services/api/tests/test_reports.py",
            "mode": "add",
            "content": TEST_REPORTS_CONTENT
        }
    ]
    
    upload_draft(task_id, files)
    
    # Optional: Dry-run first to see diff
    print("\n📋 Dry-run (preview changes)...")
    dry_result = apply_changes(task_id, approve=False)
    if "diff_summary" in dry_result:
        print(f"  Changes: {dry_result['diff_summary']}")
    
    # Apply for real
    print("\n✅ Applying changes...")
    apply_result = apply_changes(task_id, approve=True)
    
    print("\n" + "=" * 50)
    print("✓ Build complete!")
    
    if "diff_summary" in apply_result:
        print(f"  Summary: {apply_result['diff_summary']}")
    
    if apply_result.get("git_pushed"):
        print("  📤 Changes pushed to git")
    
    print("\n💡 Next steps:")
    print(f"  1. Test: curl {API}/reports/summary")
    print("  2. Run tests: pytest services/api/tests/test_reports.py")
    

if __name__ == "__main__":
    try:
        build_reports()
    except KeyboardInterrupt:
        print("\n\n⚠ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)
