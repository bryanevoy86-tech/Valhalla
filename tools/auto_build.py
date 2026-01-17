"""
Heimdall auto-builder runner.
Uses the Builder API to automatically draft and apply code changes.

This script demonstrates how Heimdall can use the Builder API to:
1. Register as an agent
2. Create tasks
3. Upload code drafts (single files or multi-file packs)
4. Apply changes (with optional dry-run first)

Usage:
    API_BASE=http://localhost:4000 BUILDER_KEY=test123 python tools/auto_build.py
    
    # Build specific pack:
    python tools/auto_build.py reports
    python tools/auto_build.py metrics_capital
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


def open_text(path):
    """Load file content, return empty if not found"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def pack_metrics_capital():
    """
    Build capital/metrics/telemetry pack.
    Returns list of file dictionaries ready for draft upload.
    """
    # All files already exist, return existing content
    files = []
    
    # Models (should already be created)
    telemetry_model = open_text("services/api/app/models/telemetry.py")
    if telemetry_model:
        files.append({
            "path": "services/api/app/models/telemetry.py",
            "mode": "replace",
            "content": telemetry_model
        })
    
    capital_model = open_text("services/api/app/models/capital.py")
    if capital_model:
        files.append({
            "path": "services/api/app/models/capital.py",
            "mode": "replace",
            "content": capital_model
        })
    
    # Schemas
    telemetry_schema = open_text("services/api/app/schemas/telemetry.py")
    if telemetry_schema:
        files.append({
            "path": "services/api/app/schemas/telemetry.py",
            "mode": "replace",
            "content": telemetry_schema
        })
    
    capital_schema = open_text("services/api/app/schemas/capital.py")
    if capital_schema:
        files.append({
            "path": "services/api/app/schemas/capital.py",
            "mode": "replace",
            "content": capital_schema
        })
    
    # Routers
    metrics_router = open_text("services/api/app/routers/metrics.py")
    if metrics_router:
        files.append({
            "path": "services/api/app/routers/metrics.py",
            "mode": "replace",
            "content": metrics_router
        })
    
    telemetry_router = open_text("services/api/app/routers/telemetry.py")
    if telemetry_router:
        files.append({
            "path": "services/api/app/routers/telemetry.py",
            "mode": "replace",
            "content": telemetry_router
        })
    
    capital_router = open_text("services/api/app/routers/capital.py")
    if capital_router:
        files.append({
            "path": "services/api/app/routers/capital.py",
            "mode": "replace",
            "content": capital_router
        })
    
    # Jobs
    forecast_jobs = open_text("services/api/app/jobs/forecast_jobs.py")
    if forecast_jobs:
        files.append({
            "path": "services/api/app/jobs/forecast_jobs.py",
            "mode": "add",
            "content": forecast_jobs
        })
    
    freeze_jobs = open_text("services/api/app/jobs/freeze_jobs.py")
    if freeze_jobs:
        files.append({
            "path": "services/api/app/jobs/freeze_jobs.py",
            "mode": "add",
            "content": freeze_jobs
        })
    
    # Update jobs router
    jobs_router = open_text("services/api/app/routers/jobs.py")
    if jobs_router:
        files.append({
            "path": "services/api/app/routers/jobs.py",
            "mode": "replace",
            "content": jobs_router
        })
    
    # Main.py with telemetry router
    main_py = open_text("services/api/main.py")
    if main_py:
        files.append({
            "path": "services/api/main.py",
            "mode": "replace",
            "content": main_py
        })
    
    return files


def pack_tests():
    """Build test pack - returns test files"""
    files = []
    
    test_metrics = open_text("services/api/tests/test_metrics_capital.py")
    if test_metrics:
        files.append({
            "path": "services/api/tests/test_metrics_capital.py",
            "mode": "add",
            "content": test_metrics
        })
    
    return files


def draft_apply(title, files, dry_run=True):
    """
    Helper to create task, upload files, dry-run, and apply.
    
    Args:
        title: Task title
        files: List of file dicts with path, mode, content
        dry_run: If True, show diff before applying
    
    Returns:
        Final apply result
    """
    ensure_registered()
    
    scope = ", ".join(f["path"] for f in files[:3])
    if len(files) > 3:
        scope += f" + {len(files)-3} more"
    
    task_id = create_task(title, scope)
    upload_draft(task_id, files)
    
    if dry_run:
        print("\n📋 Dry-run (preview changes)...")
        dry_result = apply_changes(task_id, approve=False)
        if "diff_summary" in dry_result:
            print(f"  Changes: {dry_result['diff_summary']}")
        
        # Ask user to confirm
        confirm = input("\n👉 Apply changes? [y/N]: ")
        if confirm.lower() != 'y':
            print("⚠ Cancelled by user")
            return None
    
    print("\n✅ Applying changes...")
    result = apply_changes(task_id, approve=True)
    
    print("\n" + "=" * 50)
    print("✓ Build complete!")
    
    if "diff_summary" in result:
        print(f"  Summary: {result['diff_summary']}")
    
    if result.get("git_pushed"):
        print("  📤 Changes pushed to git")
    
    return result


def build_reports():
    """Build reports feature"""
    print("\n🤖 Heimdall Auto-Builder: Reports Feature")
    print("=" * 50)
    
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
    
    result = draft_apply("Add /reports/summary endpoint", files)
    
    if result:
        print("\n💡 Next steps:")
        print(f"  1. Test: curl {API}/reports/summary")
        print("  2. Run tests: pytest services/api/tests/test_reports.py")


def pack_grants():
    """Build grants pack - returns all grants-related files"""
    files = []
    
    # Models
    grants_model = open_text("services/api/app/models/grants.py")
    if grants_model:
        files.append({
            "path": "services/api/app/models/grants.py",
            "mode": "add",
            "content": grants_model
        })
    
    # Schemas
    grants_schema = open_text("services/api/app/schemas/grants.py")
    if grants_schema:
        files.append({
            "path": "services/api/app/schemas/grants.py",
            "mode": "add",
            "content": grants_schema
        })
    
    # Router
    grants_router = open_text("services/api/app/routers/grants.py")
    if grants_router:
        files.append({
            "path": "services/api/app/routers/grants.py",
            "mode": "add",
            "content": grants_router
        })
    
    # Jobs
    grant_jobs = open_text("services/api/app/jobs/grant_jobs.py")
    if grant_jobs:
        files.append({
            "path": "services/api/app/jobs/grant_jobs.py",
            "mode": "add",
            "content": grant_jobs
        })
    
    # Update jobs router
    jobs_router = open_text("services/api/app/routers/jobs.py")
    if jobs_router:
        files.append({
            "path": "services/api/app/routers/jobs.py",
            "mode": "replace",
            "content": jobs_router
        })
    
    # Main.py with grants router
    main_py = open_text("services/api/main.py")
    if main_py:
        files.append({
            "path": "services/api/main.py",
            "mode": "replace",
            "content": main_py
        })
    
    # Tests
    test_grants = open_text("services/api/tests/test_grants.py")
    if test_grants:
        files.append({
            "path": "services/api/tests/test_grants.py",
            "mode": "add",
            "content": test_grants
        })
    
    return files


def build_metrics_capital():
    """Build capital/metrics/telemetry pack"""
    print("\n🤖 Heimdall Auto-Builder: Capital/Metrics/Telemetry Pack")
    print("=" * 50)
    
    files = pack_metrics_capital()
    if not files:
        print("❌ No files found to build")
        return
    
    print(f"📦 Building {len(files)} files...")
    
    result = draft_apply("Add capital intake, metrics, and telemetry system", files, dry_run=False)
    
    if result:
        print("\n💡 Next steps:")
        print(f"  1. Run migration: alembic upgrade head")
        print(f"  2. Test metrics: curl {API}/metrics")
        print(f"  3. Test capital: curl -H 'X-API-Key: {KEY}' {API}/capital/intake")
        print(f"  4. Run tests: pytest services/api/tests/test_metrics_capital.py")


def pack_matching():
    """Build matching pack - returns all buyer-deal matching files"""
    def txt(p):
        try:
            return open(p, "r", encoding="utf-8").read()
        except FileNotFoundError:
            return ""
    
    files = [
        {"path": "services/api/app/models/match.py", "mode": "add", "content": txt("services/api/app/models/match.py")},
        {"path": "services/api/app/schemas/match.py", "mode": "add", "content": txt("services/api/app/schemas/match.py")},
        {"path": "services/api/app/core/matcher.py", "mode": "add", "content": txt("services/api/app/core/matcher.py")},
        {"path": "services/api/app/routers/buyers.py", "mode": "add", "content": txt("services/api/app/routers/buyers.py")},
        {"path": "services/api/app/routers/deals.py", "mode": "add", "content": txt("services/api/app/routers/deals.py")},
        {"path": "services/api/app/routers/match.py", "mode": "replace", "content": txt("services/api/app/routers/match.py")},
        {"path": "services/api/app/jobs/match_jobs.py", "mode": "add", "content": txt("services/api/app/jobs/match_jobs.py")},
        {"path": "services/api/alembic/versions/20251103_v3_6_buyer_matching.py", "mode": "add", "content": txt("services/api/alembic/versions/20251103_v3_6_buyer_matching.py")},
        {"path": "services/api/tests/test_matching.py", "mode": "add", "content": txt("services/api/tests/test_matching.py")},
    ]
    
    # Auto-wire routers in main.py
    main = txt("services/api/main.py")
    if "buyers_router" not in main or "deals_router" not in main or "match_router" not in main:
        files.append({"path": "services/api/main.py", "mode": "replace", "content": main})
    
    # Update jobs router
    jobs = txt("services/api/app/routers/jobs.py")
    if jobs and "sweep_top_matches" not in jobs:
        files.append({"path": "services/api/app/routers/jobs.py", "mode": "replace", "content": jobs})
    
    return files


def build_grants():
    """Build grants pack"""
    print("\n🤖 Heimdall Auto-Builder: Grant Pack Generator")
    print("=" * 50)
    
    files = pack_grants()
    if not files:
        print("❌ No files found to build")
        return
    
    print(f"📦 Building {len(files)} files...")
    
    result = draft_apply("Add grants pack with scoring and PDF export", files, dry_run=False)
    
    if result:
        print("\n💡 Next steps:")
        print(f"  1. Run migration: alembic upgrade head")
        print(f"  2. Test sources: curl -H 'X-API-Key: {KEY}' {API}/grants/sources")


def build_matching():
    """Build buyer matching engine"""
    print("\n🤖 Heimdall Auto-Builder: Buyer Matching Engine")
    print("=" * 50)
    
    files = pack_matching()
    if not files:
        print("❌ No files found to build")
        return
    
    print(f"📦 Building {len(files)} files...")
    
    result = draft_apply("Add buyer-deal matching engine with fuzzy scoring", files, dry_run=False)
    
    if result:
        print("\n💡 Next steps:")
        print(f"  1. Run migration: alembic upgrade head")
        print(f"  2. Test buyers: curl -H 'X-API-Key: {KEY}' {API}/buyers")
        print(f"  3. Test matching: curl -X POST -H 'X-API-Key: {KEY}' {API}/match/compute")
        print(f"  4. Run tests: pytest services/api/tests/test_matching.py")
        print(f"  3. Test generate: curl -X POST -H 'X-API-Key: {KEY}' {API}/grants/generate")
        print(f"  4. Run tests: pytest services/api/tests/test_grants.py")


def pack_intake_notify():
    """Build intake + notifications pack - returns all related files"""
    def txt(p):
        try:
            return open(p, "r", encoding="utf-8").read()
        except FileNotFoundError:
            return ""

    files = [
        {"path": "services/api/app/models/intake.py", "mode": "add", "content": txt("services/api/app/models/intake.py")},
        {"path": "services/api/app/models/notify.py", "mode": "add", "content": txt("services/api/app/models/notify.py")},
        {"path": "services/api/app/schemas/intake.py", "mode": "add", "content": txt("services/api/app/schemas/intake.py")},
        {"path": "services/api/app/schemas/notify.py", "mode": "add", "content": txt("services/api/app/schemas/notify.py")},
        {"path": "services/api/app/core/normalizer.py", "mode": "add", "content": txt("services/api/app/core/normalizer.py")},
        {"path": "services/api/app/routers/intake.py", "mode": "add", "content": txt("services/api/app/routers/intake.py")},
        {"path": "services/api/app/routers/notify.py", "mode": "add", "content": txt("services/api/app/routers/notify.py")},
        {"path": "services/api/app/jobs/notification_jobs.py", "mode": "add", "content": txt("services/api/app/jobs/notification_jobs.py")},
        {"path": "services/api/app/routers/jobs.py", "mode": "replace", "content": txt("services/api/app/routers/jobs.py")},
        {"path": "services/api/alembic/versions/20251103_v3_7_intake_notify.py", "mode": "add", "content": txt("services/api/alembic/versions/20251103_v3_7_intake_notify.py")},
        {"path": "services/api/tests/test_intake_notify.py", "mode": "add", "content": txt("services/api/tests/test_intake_notify.py")},
    ]

    # auto-wire main.py includes if missing
    main = txt("services/api/main.py")
    inc = "\nfrom app.routers.intake import router as intake_router\nfrom app.routers.notify import router as notify_router\napp.include_router(intake_router, prefix=\"/api\")\napp.include_router(notify_router, prefix=\"/api\")\n"
    if "intake_router" not in main or "notify_router" not in main:
        main = main.rstrip() + "\n\n# AUTO-INCLUDE (intake/notify)\n" + inc
        files.append({"path": "services/api/main.py", "mode": "replace", "content": main})

    return files


def build_intake_notify():
    """Build intake + notifications pack"""
    print("\n🤖 Heimdall Auto-Builder: Intake + Notifications Pack")
    print("=" * 50)

    files = pack_intake_notify()
    if not files:
        print("❌ No files found to build")
        return

    print(f"📦 Building {len(files)} files...")

    result = draft_apply("Auto-build: intake + notifications", files, dry_run=False)

    if result:
        print("\n💡 Next steps:")
        print(f"  1. Run migration: alembic upgrade head")
        print(f"  2. Test lead intake: curl -H 'X-API-Key: {KEY}' -H 'Content-Type: application/json' -d '{{}}' {API}/intake/leads")
        print(f"  3. Test notify queue: curl -H 'X-API-Key: {KEY}' -H 'Content-Type: application/json' -d '{{\"payload\":{{\"ping\":\"ok\"}}}}' {API}/notify/webhook")
        print(f"  4. Dispatch: curl -X POST -H 'X-API-Key: {KEY}' {API}/jobs/notify/dispatch")
        print(f"  5. Run tests: pytest services/api/tests/test_intake_notify.py")

if __name__ == "__main__":
    pack = sys.argv[1] if len(sys.argv) > 1 else "reports"
    
    try:
        if pack == "reports":
            build_reports()
        elif pack in ["metrics_capital", "capital", "metrics"]:
            build_metrics_capital()
        elif pack == "grants":
            build_grants()
        elif pack == "matching":
            build_matching()
        elif pack in ["intake_notify", "intake", "notify"]:
            build_intake_notify()
        else:
            print(f"❌ Unknown pack: {pack}")
            print("Available packs: reports, metrics_capital, grants, matching, intake_notify")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
