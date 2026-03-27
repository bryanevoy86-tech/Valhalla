# --- Auto-PR: status + run-now (enqueues job) ---
@app.get("/admin/heimdall/api/autopr/status")
def autopr_status():
    cfg = _cfg_dict()
    path = _P((cfg.get("autopr", {}) or {}).get("status_file", "dist/docs/auto_pr_status.json"))
    js = {}
    if path.exists():
        try:
            js = _json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            js = {"ok": False, "error": "could not parse status file"}
    return {"ok": True, "status": js, "config": (cfg.get("autopr", {}) or {})}


@app.post("/admin/heimdall/autopr/run")
def autopr_run_now():
    cfg = _cfg_dict()
    task = {
        "type": "job",
        "name": "autopr_now",
        "shell": "python scripts/ci/auto_pr.py",
        "sandbox": False,
        "timeout": 180,
    }
    w = _enqueue_task_file(cfg, task)
    return {"ok": True, "written": [w]}


# --- Alerts: status + test
@app.get("/admin/heimdall/api/alerts/status")
def alerts_status():
    try:
        p = _P("heimdall/state/alerts_state.json")
        st = _json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:
        st = {}
    cfg = _cfg_dict()
    return {"ok": True, "state": st, "config": cfg.get("alerts", {})}


@app.post("/admin/heimdall/api/alerts/test")
def alerts_test():
    from backend.notify import post_discord

    ok = post_discord("🔔 Heimdall test alert: notifications are working.")
    return {"ok": True, "delivered": bool(ok)}


# --- FastAPI app setup ---
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse

app = FastAPI(title="Valhalla API")

# Stub HeimdallAuthMiddleware if missing
try:
    from auth import HeimdallAuthMiddleware
except ImportError:

    class HeimdallAuthMiddleware:
        def __init__(self, app):
            pass


# Protect all /admin/* routes with role-aware middleware
app.add_middleware(HeimdallAuthMiddleware)

# --- Health & Metrics ---
import datetime as _dt
import json as _json
import os as _os
import time as _t
from pathlib import Path as _P


def _cfg_dict():
    if CONFIG_PATH.exists():
        return _json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def _queue_counts(cfg) -> dict:
    qdir = _P(cfg.get("queue_dir", "heimdall/queue"))
    qdir.mkdir(parents=True, exist_ok=True)
    done_suf = cfg.get("processed_suffix", ".done.yaml")
    proc_suf = cfg.get("processing_suffix", ".working")
    pending = working = done = errs = 0
    for p in qdir.glob("*.yaml"):
        n = p.name
        if n.endswith(done_suf):
            done += 1
        elif n.endswith(".error.yaml"):
            errs += 1
        elif n.endswith(proc_suf + ".yaml"):
            working += 1
        else:
            pending += 1
    return {"pending": pending, "working": working, "done": done, "errors": errs}


def _heartbeat_info(cfg) -> dict:
    hb_file = _P(
        (cfg.get("health", {}) or {}).get("heartbeat_file", "heimdall/state/worker_heartbeat.json")
    )
    if not hb_file.exists():
        return {"present": False, "age_seconds": None, "raw": None}
    try:
        js = _json.loads(hb_file.read_text(encoding="utf-8"))
        age = max(0.0, _t.time() - float(js.get("ts", 0)))
        return {"present": True, "age_seconds": age, "raw": js}
    except Exception:
        return {"present": True, "age_seconds": None, "raw": None}


@app.get("/healthz")
def healthz():
    cfg = _cfg_dict()
    return {
        "ok": True,
        "time": _dt.datetime.now().isoformat(timespec="seconds"),
        "queue": _queue_counts(cfg),
    }


@app.get("/readyz")
def readyz():
    cfg = _cfg_dict()
    hb = _heartbeat_info(cfg)
    max_age = int((cfg.get("health", {}) or {}).get("ready_heartbeat_max_age_seconds", 45))
    hb_ok = hb["present"] and (hb["age_seconds"] is not None) and (hb["age_seconds"] <= max_age)

    db_ok = True
    need_db = bool((cfg.get("health", {}) or {}).get("ready_require_db", False))
    if need_db and _os.getenv("DATABASE_URL"):
        try:
            from backend.db import get_conn

            with get_conn(_os.getenv("DATABASE_URL")) as conn, conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
        except Exception:
            db_ok = False

    ok = hb_ok and db_ok
    status = 200 if ok else 503
    return JSONResponse(
        {
            "ok": ok,
            "worker_heartbeat_ok": hb_ok,
            "worker_heartbeat_age_seconds": hb.get("age_seconds"),
            "db_ok": db_ok,
            "queue": _queue_counts(cfg),
        },
        status_code=status,
    )


@app.get("/metrics")
def metrics_json():
    cfg = _cfg_dict()
    hb = _heartbeat_info(cfg)
    met = {}
    try:
        mpath = _P(cfg.get("metrics_file", "heimdall/state/metrics.json"))
        if mpath.exists():
            met = _json.loads(mpath.read_text(encoding="utf-8"))
    except Exception:
        met = {}
    return {
        "queue": _queue_counts(cfg),
        "heartbeat_age_seconds": hb.get("age_seconds"),
        "metrics": met,
    }


@app.get("/metrics/prometheus", response_class=PlainTextResponse)
def metrics_prom():
    cfg = _cfg_dict()
    hb = _heartbeat_info(cfg)
    q = _queue_counts(cfg)
    lines = []

    def put(name, val, typ="gauge", help_txt=""):
        if help_txt:
            lines.append(f"# HELP {name} {help_txt}")
        if typ:
            lines.append(f"# TYPE {name} {typ}")
        lines.append(f"{name} {val}")

    put("heimdall_queue_pending", q["pending"], "gauge", "Pending queue items")
    put("heimdall_queue_working", q["working"], "gauge", "Working (claimed) items")
    put("heimdall_queue_done", q["done"], "gauge", "Done items sitting in queue dir")
    put("heimdall_queue_errors", q["errors"], "gauge", "Error items in queue dir")
    put(
        "heimdall_worker_heartbeat_age_seconds",
        hb.get("age_seconds") or 1e9,
        "gauge",
        "Age of last worker heartbeat",
    )
    try:
        mpath = _P(cfg.get("metrics_file", "heimdall/state/metrics.json"))
        if mpath.exists():
            m = _json.loads(mpath.read_text(encoding="utf-8"))
            put(
                "heimdall_processed_total",
                int(m.get("processed_total", 0)),
                "counter",
                "Total processed",
            )
            put("heimdall_errors_total", int(m.get("errors_total", 0)), "counter", "Total errors")
    except Exception:
        pass
    return "\n".join(lines) + "\n"


import json
import pkgutil
import time
import time as _time
from importlib import import_module
from typing import Optional

import yaml
import yaml as _yaml
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.notify import notify_test

app = FastAPI(title="Valhalla API")
# Protect all /admin/* routes with role-aware middleware
app.add_middleware(HeimdallAuthMiddleware)


# --- Publish Now API ---
@app.post("/admin/heimdall/publish-now")
async def admin_publish_now(req: Request):
    # Load config (same pattern as /admin/notify/test)
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    else:
        cfg = {}
    body = await req.json()
    # Build task
    task = {"type": "publish"}
    if body.get("name"):
        task["name"] = body["name"]
    if body.get("note"):
        task["note"] = body["note"]
    if body.get("from_job"):
        task["from_job"] = body["from_job"]
    if body.get("include_stdout"):
        task["include_stdout"] = True
    if body.get("include_stderr"):
        task["include_stderr"] = True
    if isinstance(body.get("sources"), list) and body["sources"]:
        task["sources"] = body["sources"]
    if isinstance(body.get("strip_prefixes"), list) and body["strip_prefixes"]:
        task["strip_prefixes"] = body["strip_prefixes"]

    # Validate before enqueue (same validator used by worker)
    from backend.heimdall_validate import validate_task

    ok, errs, warns = validate_task(task)
    if not ok:
        return {"ok": False, "errors": errs, "warnings": warns}

    # Enqueue
    qdir = _P(cfg.get("queue_dir", "heimdall/queue"))
    qdir.mkdir(parents=True, exist_ok=True)
    ts = int(_time.time())
    final = qdir / f"publish_{ts}.yaml"
    tmp = qdir / f".publish_{ts}.tmp"
    tmp.write_text(_yaml.safe_dump(task, sort_keys=False), encoding="utf-8")
    tmp.replace(final)

    return {"ok": True, "file": str(final), "warnings": warns}


from pathlib import Path

from fastapi import FastAPI

app = FastAPI(title="Valhalla API")


# Notification test endpoint (must be after app = FastAPI)
@app.post("/admin/notify/test")
async def admin_notify_test():
    # Reuse existing config loader
    if CONFIG_PATH.exists():
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    else:
        cfg = {}
    return await notify_test(cfg)


from fastapi import FastAPI

APP_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_ROOT / "heimdall" / "agent.config.json"

# validator
# UI router
from backend.admin_ui import router as admin_ui_router
from backend.heimdall_validate import lint_task_yaml_str, validate_task

app = FastAPI(title="Valhalla API")

# mount static for admin UI
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/health")
def health():
    return {"ok": True}


def _autoload_generated_routes() -> int:
    base_pkg = "backend.generated_routes"
    base_path = Path(__file__).parent / "generated_routes"
    loaded = 0
    if not base_path.exists():
        return 0
    for m in pkgutil.iter_modules([str(base_path)]):
        mod_name = f"{base_pkg}.{m.name}"
        mod = import_module(mod_name)
        router = getattr(mod, "router", None)
        if router is not None:
            app.include_router(router)
            loaded += 1
    return loaded


# initial load
_autoload_generated_routes()


def _load_cfg() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def _tail_file(path: Path, max_lines: int = 200) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return lines[-max_lines:]


@app.post("/tasks")
def post_task(task: dict):
    """
    Accepts a Heimdall task (JSON) and writes it to the queue as YAML.
    Validates before enqueue to catch mistakes early.
    """
    ok, errs, warns = validate_task(task)
    if not ok:
        return {"queued": False, "errors": errs, "warnings": warns}

    cfg = _load_cfg()
    qdir = APP_ROOT / cfg.get("queue_dir", "heimdall/queue")
    qdir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    ttype = task.get("type", "task")
    fname = qdir / f"{ttype}_{ts}.yaml"
    tmp = qdir / f".{ttype}_{ts}.tmp"
    tmp.write_text(yaml.safe_dump(task, sort_keys=False), encoding="utf-8")
    tmp.replace(fname)
    return {"queued": True, "file": str(fname.relative_to(APP_ROOT)), "warnings": warns}


@app.post("/admin/reload")
def admin_reload():
    loaded = _autoload_generated_routes()
    return {"reloaded": loaded}


@app.get("/admin/heimdall/metrics")
def get_metrics():
    cfg = _load_cfg()
    mpath = APP_ROOT / cfg.get("metrics_file", "heimdall/state/metrics.json")
    if not mpath.exists():
        return {"note": "metrics not created yet"}
    try:
        return json.loads(mpath.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(500, f"failed to read metrics: {e}")


@app.get("/admin/heimdall/logs")
def get_logs(lines: int = Query(200, ge=10, le=2000)):
    cfg = _load_cfg()
    lpath = APP_ROOT / cfg.get("log_file", "heimdall_action.log")
    data = _tail_file(lpath, max_lines=lines)
    return {"lines": data, "file": str(lpath.relative_to(APP_ROOT))}


@app.post("/admin/lint")
def admin_lint(task: Optional[dict] = None, yaml_text: Optional[str] = None):
    """
    Lint a task without enqueuing. Send either JSON 'task' or plain 'yaml_text'.
    """
    if yaml_text is not None:
        return lint_task_yaml_str(yaml_text)
    if task is None:
        raise HTTPException(400, "provide JSON 'task' or 'yaml_text'")
    ok, errs, warns = validate_task(task)
    return {"ok": ok, "errors": errs, "warnings": warns, "normalized": task}


# plug in the HTML admin UI
app.include_router(admin_ui_router)


# --- Knowledge: stats API (reads index.jsonl)
@app.get("/admin/heimdall/api/knowledge/stats")
def knowledge_stats():
    idx = _P("knowledge/index.jsonl")
    cats = {}
    total = 0
    if idx.exists():
        with idx.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    js = _json.loads(line)
                    cat = js.get("category", "uncategorized")
                    cats[cat] = cats.get(cat, 0) + 1
                    total += 1
                except Exception:
                    pass
    return {"ok": True, "total": total, "by_category": cats}


# --- Queue Status & Pause/Resume Endpoints ---
import sys

sys.path.append(str(APP_ROOT / "services" / "api"))
try:
    from backend.heimdall_service import (
        get_queue_status,
        is_queue_paused,
        pause_queue,
        resume_queue,
    )
except ImportError:
    # Stubs if heimdall_service not available
    def get_queue_status():
        return {
            "paused": False,
            "active_workers": 0,
            "last_heartbeat": None,
            "throttle": 0,
            "max_concurrency": 1,
            "last_status": "idle",
        }

    def pause_queue():
        pass

    def resume_queue():
        pass

    def is_queue_paused():
        return False


@app.get("/admin/heimdall/queue-status")
def admin_queue_status():
    """Return current queue status for admin UI."""
    return get_queue_status()


@app.post("/admin/heimdall/pause-queue")
def admin_pause_queue():
    """Pause the queue (no new jobs processed)."""
    pause_queue()
    return {"ok": True, "paused": is_queue_paused()}


@app.post("/admin/heimdall/resume-queue")
def admin_resume_queue():
    """Resume the queue (allow jobs to process)."""
    resume_queue()
    return {"ok": True, "paused": is_queue_paused()}


@app.get("/queue/status")
def queue_status():
    from backend.heimdall_service import get_queue_status

    return get_queue_status()


@app.post("/queue/pause")
def queue_pause():
    from backend.heimdall_service import pause_queue

    pause_queue()
    return {"ok": True, "paused": True}


@app.post("/queue/resume")
def queue_resume():
    from backend.heimdall_service import resume_queue

    resume_queue()
    return {"ok": True, "paused": False}
