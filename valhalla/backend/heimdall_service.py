from backend.notify import post_discord


# --- Alerts helpers ---
def _alerts_cfg(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return cfg.get("alerts", {}) or {}


def _alerts_state_path() -> Path:
    return Path("heimdall/state/alerts_state.json")


def _events_path(cfg: Dict[str, Any]) -> Path:
    return Path(cfg.get("events_file", "heimdall/state/events.jsonl"))


def _read_recent_error_events(cfg: Dict[str, Any], minutes: int) -> int:
    import json
    import time

    cutoff = time.time() - minutes * 60
    cnt = 0
    p = _events_path(cfg)
    if not p.exists():
        return 0
    try:
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    js = json.loads(line.strip())
                except Exception:
                    continue
                if float(js.get("ts", 0)) < cutoff:
                    continue
                ev = str(js.get("event", ""))
                if "error" in ev.lower():
                    cnt += 1
    except Exception:
        pass
    return cnt


def _read_alert_state() -> Dict[str, Any]:
    p = _alerts_state_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _write_alert_state(st: Dict[str, Any]) -> None:
    p = _alerts_state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, indent=2), encoding="utf-8")


# --- Alert watcher coroutine ---
import hashlib


async def _alert_watcher(cfg: Dict[str, Any]) -> None:
    a = _alerts_cfg(cfg)
    if not a.get("enabled", False):
        return
    interval = int(a.get("interval_seconds", 60))
    suppress = int(a.get("repeat_suppress_seconds", 900))
    while True:
        try:
            qdir = Path(cfg["queue_dir"])
            q = get_queue_status()
            hb_age = None
            try:
                hb = json.loads(Path("heimdall/state/heartbeat.json").read_text(encoding="utf-8"))
                hb_age = max(0.0, time.time() - float(hb.get("ts", 0)))
            except Exception:
                hb_age = 1e9
            recent_errs = _read_recent_error_events(
                cfg, int(a.get("error_events_window_minutes", 10))
            )

            issues = []
            if q["paused"]:
                pass
            elif q["active_workers"] == 0:
                issues.append("No active workers")
            if q["paused"]:
                issues.append("Queue paused")
            if q["last_status"] == "paused":
                issues.append("Queue status: paused")
            if q["last_status"] == "idle":
                pass
            if q["last_status"] == "active":
                pass
            if q.get("pending", 0) >= int(a.get("backlog_pending_warn", 150)):
                issues.append(f"Backlog high: pending={q.get('pending',0)}")
            if hb_age is None or hb_age > float(a.get("heartbeat_max_age_warn_seconds", 120)):
                issues.append(f"Worker heartbeat stale: age={int(hb_age or 0)}s")
            if recent_errs >= int(a.get("error_events_warn", 5)):
                issues.append(
                    f"Errors in last {a.get('error_events_window_minutes',10)}m: {recent_errs}"
                )

            st = _read_alert_state()
            last_hash = st.get("last_hash")
            last_ts = float(st.get("last_ts", 0))
            summary = " | ".join(issues) if issues else ""
            cur_hash = hashlib.sha256(summary.encode("utf-8")).hexdigest() if summary else None

            if issues:
                should_send = (cur_hash != last_hash) or ((time.time() - last_ts) >= suppress)
                if should_send:
                    text = f"**Heimdall Alert**: {summary}\nQueue: pending {q.get('pending',0)}, working {q.get('active_workers',0)}, status {q.get('last_status','?')}"
                    post_discord(text)
                    _write_alert_state(
                        {"last_hash": cur_hash, "last_ts": time.time(), "last_summary": summary}
                    )
            else:
                if last_hash:
                    _write_alert_state({})
        except Exception:
            log.exception("alert watcher failed")
        await asyncio.sleep(interval)


import json
from typing import List

import httpx


# Stub for jinja_env and write_preview_or_apply
def jinja_env():
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    return Environment(
        loader=FileSystemLoader("backend/templates"), autoescape=select_autoescape(["html", "xml"])
    )


def write_preview_or_apply(out_file, code, cfg, template_type, name):
    out_file.write_text(code, encoding="utf-8")


# --- job runner ---
import asyncio
import logging
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

import yaml

# Setup logger
log = logging.getLogger("heimdall")
log.setLevel(logging.INFO)


# Stub for sanitize_name if not defined elsewhere
def sanitize_name(name):
    return str(name).replace(" ", "_").replace("-", "_")


# --- Rate limit, pause/resume, queue status globals ---
queue_paused = threading.Event()
queue_paused.clear()  # Not paused by default
queue_status = {
    "paused": False,
    "active_workers": 0,
    "last_heartbeat": None,
    "throttle": 0,
    "max_concurrency": 1,
    "last_status": "idle",
}


def get_rate_limit_cfg(cfg: Dict[str, Any]):
    rl = cfg.get("rate_limit", {}) or {}
    return {
        "max_concurrency": int(rl.get("max_concurrency", 1)),
        "throttle_seconds": float(rl.get("throttle_seconds", 0)),
        "pause_enabled": bool(rl.get("pause_enabled", True)),
    }


def pause_queue():
    queue_paused.set()
    queue_status["paused"] = True
    queue_status["last_status"] = "paused"


def resume_queue():
    queue_paused.clear()
    queue_status["paused"] = False
    queue_status["last_status"] = "resumed"


def is_queue_paused():
    return queue_paused.is_set()


def update_queue_heartbeat():
    queue_status["last_heartbeat"] = time.time()


def get_queue_status():
    return dict(queue_status)

    jobs_cfg = cfg.get("jobs", {}) or {}
    if not jobs_cfg.get("enabled", True):
        raise RuntimeError("jobs are disabled in config")
    name = sanitize_name(task.get("name", "job"))
    shell_script = task.get("shell")
    py_code = task.get("python")
    timeout = int(task.get("timeout") or jobs_cfg.get("max_seconds", 900))
    cwd_rel = task.get("cwd")
    cwd = (Path(".").resolve() / cwd_rel).resolve() if cwd_rel else Path(".").resolve()
    cwd.mkdir(parents=True, exist_ok=True)

    jobs_root = Path(".").resolve() / jobs_cfg.get("jobs_dir", "generated/jobs")
    ts = int(time.time())
    run_dir = jobs_root / name / str(ts)
    run_dir.mkdir(parents=True, exist_ok=True)

    # --- New CHUNK 73.2 Logic ---

    # --- New CHUNK 73.2 Logic ---


def after_changes_reload(cfg: Dict[str, Any]):
    if cfg.get("dry_run", True):
        return
    if cfg.get("auto_reload", False):
        try:
            url = cfg.get("auto_reload_url", "http://api:8000/admin/reload")
            r = httpx.post(url, timeout=5)
            log.info("Auto-reload %s → %s", url, r.status_code)
        except Exception:
            log.exception("Auto-reload failed")


def enqueue_task(task: Dict[str, Any], cfg: Dict[str, Any]):
    qdir = Path(cfg["queue_dir"])
    qdir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    ttype = task.get("type", "task")
    tmp = qdir / f".{ttype}_{ts}.tmp"
    final = qdir / f"{ttype}_{ts}.yaml"
    tmp.write_text(yaml.safe_dump(task, sort_keys=False), encoding="utf-8")
    tmp.replace(final)
    log.info("Scheduled task → %s", final)


# ---------- templates helpers ----------
_PG_TYPE_TO_PY = {
    "bigserial": "int",
    "bigint": "int",
    "serial": "int",
    "integer": "int",
    "int": "int",
    "smallint": "int",
    "text": "str",
    "string": "str",
    "varchar": "str",
    "bool": "bool",
    "boolean": "bool",
    "numeric": "float",
    "decimal": "float",
    "float": "float",
    "double": "float",
    "timestamp": "datetime",
    "timestamptz": "datetime",
    "datetime": "datetime",
    "date": "date",
    "jsonb": "dict",
    "json": "dict",
    "dict": "dict",
    "list": "list",
    "array": "list",
}


def _format_default_sql(val: Any) -> str:
    if isinstance(val, str):
        low = val.lower()
        if low in {"now()", "current_timestamp", "true", "false"} or low.endswith("()"):
            return val
        return f"'{val}'"
    return str(val)


def _py_type_for(pg_type: str, not_null: bool) -> str:
    base = _PG_TYPE_TO_PY.get(pg_type.lower(), "Any")
    if not not_null and base not in {"Any"}:
        return f"Optional[{base}]"
    return base


def _py_default_for(default: Any):
    if default is None:
        return None
    if isinstance(default, str):
        low = default.lower()
        if low.endswith("()") or low in {"now()", "current_timestamp"}:
            return None
        if low in {"true", "false"}:
            return True if low == "true" else False
        return f"'{default}'"
    return default


# ---------- route scaffolder ----------
async def process_scaffold_route(task: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    name = sanitize_name(task.get("name", "route"))
    method = str(task.get("method", "GET")).upper()
    path = task.get("path", f"/{name}")
    prefix = task.get("prefix", "")
    tag = task.get("tag", name.capitalize())
    response = task.get("response", {"ok": True})

    env = jinja_env()
    tpl = env.get_template("backend/route.py.j2")
    code = tpl.render(
        prefix=prefix,
        tag=tag,
        method=method,
        path=path,
        func_name=name,
        response=json.dumps(response),
    )

    out_dir = Path(cfg["generated_routes_dir"])
    out_file = out_dir / f"{name}.py"
    write_preview_or_apply(out_file, code, cfg, "route.py", name)


# ---------- CRUD scaffolder ----------
async def process_scaffold_crud(task: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    """
    YAML:
      type: scaffold_crud
      resource: todo
      storage: memory | db   # default memory
      table: todos           # required if storage=db (else defaults to {resource}s)
      prefix: /todos         # optional; default "/{resource}s"
      tag: Todos             # optional
      fields:
        - { name: title, type: text }
        - { name: done,  type: bool, default: false }
    """
    resource = sanitize_name(task.get("resource") or task.get("name", "item"))
    storage = (task.get("storage") or "memory").lower()
    prefix = task.get("prefix", f"/{resource}s")
    tag = task.get("tag", f"{resource.capitalize()} CRUD")
    fields_cfg: List[Dict[str, Any]] = task.get("fields", [])

    # Build pydantic fields
    fields = []
    for col in fields_cfg:
        fname = sanitize_name(col["name"])
        pg_type = str(col.get("type", "text"))
        py_type = _PG_TYPE_TO_PY.get(pg_type.lower(), "str")
        default = _py_default_for(col.get("default"))
        fields.append({"name": fname, "py_type": py_type, "default": default})

    env = jinja_env()
    out_dir = Path(cfg["generated_routes_dir"])

    if storage == "db":
        table = task.get("table", f"{resource}s")
        cols_list = ["id"] + [f["name"] for f in fields]
        cols_csv = ", ".join(cols_list)
        insert_cols = [f["name"] for f in fields]
        insert_cols_csv = ", ".join(insert_cols)
        placeholders = ", ".join(["%s"] * len(insert_cols))

        tpl = env.get_template("backend/crud_db_route.py.j2")
        code = tpl.render(
            prefix=prefix,
            tag=tag,
            resource=resource,
            item_create_class=f"{resource.capitalize()}Create",
            item_class=f"{resource.capitalize()}Item",
            fields=fields,
            table=table,
            cols_csv=cols_csv,
            cols_list=", ".join(f'"{c}"' if not c.isidentifier() else f'"{c}"' for c in cols_list),
            insert_cols_csv=insert_cols_csv,
            placeholders=placeholders,
        )
        out_file = out_dir / f"{resource}_crud_db.py"
        write_preview_or_apply(out_file, code, cfg, "route.py", f"{resource}_crud_db")
    else:
        # in-memory version (from CHUNK 61)
        tpl = env.get_template("backend/crud_route.py.j2")
        code = tpl.render(
            prefix=prefix,
            tag=tag,
            resource=resource,
            item_create_class=f"{resource.capitalize()}Create",
            item_class=f"{resource.capitalize()}Item",
            fields=fields,
        )
        out_file = out_dir / f"{resource}_crud.py"
        write_preview_or_apply(out_file, code, cfg, "route.py", f"{resource}_crud")


# ---------- model + migration scaffolder ----------
async def process_scaffold_model(task: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    name = sanitize_name(task.get("name", "Model"))
    table = task.get("table", name)
    columns: List[Dict[str, Any]] = task.get("columns", [])

    fields = []
    statements = []
    for col in columns:
        col_name = col.get("name")
        pg_type = str(col.get("type", "text"))
        py_type = _PG_TYPE_TO_PY.get(pg_type.lower(), "str")
        py_default = _py_default_for(col.get("default"))
        fields.append({"name": col_name, "py_type": py_type, "default": py_default})
        not_null = col.get("not_null", False)
        default = col.get("default")
        primary = col.get("primary_key", False)
        parts = [f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col_name} {pg_type}"]
        if not_null:
            parts.append("NOT NULL")
        if default is not None:
            parts.append(f"DEFAULT {_format_default_sql(default)}")
        statements.append(" ".join(parts) + ";")
        if primary:
            statements.append(
                f"DO $$ BEGIN "
                f"IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{table}_pkey') THEN "
                f"ALTER TABLE {table} ADD CONSTRAINT {table}_pkey PRIMARY KEY ({col_name}); "
                f"END IF; END $$;"
            )

    env = jinja_env()
    model_tpl = env.get_template("backend/model.py.j2")
    model_code = model_tpl.render(
        class_name="".join(part.capitalize() for part in name.split("_")), fields=fields
    )
    mig_tpl = env.get_template("migrations/migration.sql.j2")
    migration_sql = mig_tpl.render(table=table, statements=statements)

    model_out = Path(cfg["generated_models_dir"]) / f"{name}.py"
    mig_out = Path(cfg["migrations_generated_dir"]) / f"{name}.sql"
    write_preview_or_apply(model_out, model_code, cfg, "model.py", name)
    write_preview_or_apply(mig_out, migration_sql, cfg, "migration.sql", name)


# ---------- migration runner ----------
async def process_run_migration(task: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    rel = task.get("file")
    if not rel:
        log.warning("run_migration task missing 'file'")
        return
    sql_path = Path(rel)
    if not sql_path.exists():
        log.warning("SQL file not found: %s", sql_path)
        return
    sql = sql_path.read_text(encoding="utf-8")
    if cfg.get("dry_run", True):
        log.info("DRY RUN: would execute migration %s (%d bytes)", sql_path, len(sql))
        return
    try:
        with get_conn(os.getenv("DATABASE_URL")) as conn, conn.cursor() as cur:
            cur.execute(sql)
        log.info("Migration applied: %s", sql_path)
    except Exception:
        log.exception("Migration failed for %s", sql_path)


# ---------- scheduler ----------
def start_scheduler(cfg: Dict[str, Any]):
    if not cfg.get("enable_scheduler", False):
        return None
    cron = cfg.get("scheduler_cron", {"hour": 3, "minute": 15})
    sched = AsyncIOScheduler()

    def nightly():
        enqueue_task(
            {
                "type": "scaffold_route",
                "name": "daily_status",
                "path": "/daily_status",
                "method": "GET",
                "response": {"ts": int(time.time()), "ok": True},
            },
            cfg,
        )

    sched.add_job(nightly, "cron", **cron)
    sched.start()
    log.info("Scheduler enabled with cron=%s", cron)
    return sched


# ---------- task router / watcher ----------
async def process_task(task_path: Path, cfg: Dict[str, Any]) -> None:
    try:
        data = yaml.safe_load(task_path.read_text(encoding="utf-8")) or {}
    except Exception:
        # YAML parse error
        log.exception("YAML parse error in %s", task_path)
        _metrics_bump(cfg, "parse_error", False)
        return
    t = data.get("type", "task")
    try:
        if t == "scaffold_route":
            await process_scaffold_route(data, cfg)
            after_changes_git(cfg)
            after_changes_reload(cfg)
            _metrics_bump(cfg, t, True)
        elif t == "scaffold_crud":
            await process_scaffold_crud(data, cfg)
            after_changes_git(cfg)
            after_changes_reload(cfg)
            _metrics_bump(cfg, t, True)
        elif t == "scaffold_model":
            await process_scaffold_model(data, cfg)
            after_changes_git(cfg)
            _metrics_bump(cfg, t, True)
        elif t == "run_migration":
            await process_run_migration(data, cfg)
            after_changes_git(cfg)
            _metrics_bump(cfg, t, True)
        elif t == "bundle":
            subs = data.get("tasks", [])
            for sub in subs:
                enqueue_task(sub, cfg)
            _metrics_bump(cfg, "bundle_enqueued", True)
        elif t == "spec":
            await process_spec(data, cfg)
            _metrics_bump(cfg, "spec_enqueued", True)
        elif t == "job":
            try:
                result = await process_job(data, cfg)
                _metrics_bump(cfg, "job", True)
                await notify_job(cfg, result, True, data)
            except Exception as e:
                log.exception("Job failed")
                _metrics_bump(cfg, "job", False)
                result = {
                    "name": data.get("name", "job"),
                    "return_code": -1,
                    "duration_ms": 0,
                    "run_dir_rel": "",
                    "stdout_rel": "",
                    "stderr_rel": "",
                }
                await notify_job(cfg, result, False, data, error_msg=str(e))
        elif t == "schedule":
            try:
                await process_schedule(data, cfg)
                _metrics_bump(cfg, "schedule", True)
            except Exception as e:
                log.exception("Schedule task failed")
                _metrics_bump(cfg, "schedule", False)
                await notify_schedule_error(cfg, data.get("name", "?"), str(e))
        else:
            log.warning("Unknown task type %r in %s", t, task_path.name)
            _metrics_bump(cfg, "unknown", False)
        done = task_path.with_suffix(cfg.get("processed_suffix", ".done.yaml"))
        task_path.rename(done)
        log.info("Processed %s -> %s", task_path.name, done.name)
    except Exception:
        log.exception("Failed processing %s", task_path)
        _metrics_bump(cfg, "exception", False)


# ---------- spec → bundle fan-out ----------
def _ensure_id_column(columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    has_id = any(c.get("name") == "id" for c in columns)
    if not has_id:
        columns = [{"name": "id", "type": "bigserial", "primary_key": True}] + columns
    return columns


def _crud_fields_from_columns(columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Stub: return columns as-is to avoid undefined variable errors
    return [c for c in columns if c.get("name") != "id"]


async def process_spec(task: Dict[str, Any], cfg: Dict[str, Any]) -> None:
    """
    YAML:
      type: spec
      name: todo
      resource: todo
      storage: db | memory
      table: todos              # for db (defaults to resource + 's')
      fields: [ {name, type, not_null?, default?, primary_key?}, ... ]
      routes: [ {name, method, path, response}, ... ]   # optional
    """
    name = sanitize_name(task.get("name") or task.get("resource", "feature"))
    resource = sanitize_name(task.get("resource") or name)
    storage = (task.get("storage") or "memory").lower()
    table = task.get("table") or (f"{resource}s" if storage == "db" else resource)

    columns = task.get("fields", [])
    columns = _ensure_id_column(columns)

    # 1) model + migration
    model = {"type": "scaffold_model", "name": name, "table": table, "columns": columns}
    enqueue_task(model, cfg)

    # 2) run migration
    mig_file = str(
        Path(cfg.get("migrations_generated_dir", "migrations/generated")) / f"{name}.sql"
    )
    runmig = {"type": "run_migration", "file": mig_file}
    enqueue_task(runmig, cfg)

    # 3) CRUD (storage-aware)
    crud = {
        "type": "scaffold_crud",
        "resource": resource,
        "storage": storage,
        "table": table if storage == "db" else None,
        "fields": _crud_fields_from_columns(columns),
    }
    # remove None keys to keep YAML pretty
    crud = {k: v for k, v in crud.items() if v is not None}
    enqueue_task(crud, cfg)

    # 4) Extra single routes (optional)
    for r in task.get("routes", []) or []:
        rr = {
            "type": "scaffold_route",
            "name": sanitize_name(r.get("name", f"{resource}_extra")),
            "method": r.get("method", "GET"),
            "path": r.get("path", f"/{resource}/extra"),
            "response": r.get("response", {"ok": True}),
        }
        enqueue_task(rr, cfg)

    log.info("Spec expanded into model + migration + CRUD (+routes)")
    # metrics recorded at the time sub-tasks are processed


async def watch_queue(cfg: Dict[str, Any]) -> None:
    qdir = Path(cfg["queue_dir"])
    qdir.mkdir(parents=True, exist_ok=True)
    poll = int(cfg.get("poll_seconds", 2))
    rl_cfg = get_rate_limit_cfg(cfg)
    queue_status["max_concurrency"] = rl_cfg["max_concurrency"]
    queue_status["throttle"] = rl_cfg["throttle_seconds"]
    log.info(
        "Watching %s every %ss (dry_run=%s, max_concurrency=%s, throttle=%ss)",
        qdir,
        poll,
        cfg.get("dry_run", True),
        rl_cfg["max_concurrency"],
        rl_cfg["throttle_seconds"],
    )

    # Start alert watcher (fire-and-forget)
    try:
        asyncio.create_task(_alert_watcher(cfg))
    except Exception:
        log.warning("could not start alert watcher", exc_info=True)

    async def worker():
        while True:
            update_queue_heartbeat()
            if is_queue_paused():
                queue_status["last_status"] = "paused"
                await asyncio.sleep(1)
                continue
            queue_status["last_status"] = "active"
            for p in sorted(qdir.glob("*.yaml")):
                if p.name.endswith(cfg.get("processed_suffix", ".done.yaml")):
                    continue
                await process_task(p, cfg)
                if rl_cfg["throttle_seconds"] > 0:
                    await asyncio.sleep(rl_cfg["throttle_seconds"])
            await asyncio.sleep(poll)

    # Launch up to max_concurrency workers
    workers = []
    for i in range(rl_cfg["max_concurrency"]):
        w = asyncio.create_task(worker())
        workers.append(w)
    queue_status["active_workers"] = len(workers)
    await asyncio.gather(*workers)


def _attach_file_logging(cfg: Dict[str, Any]):
    try:
        log_file = cfg.get("log_file", "heimdall_action.log")
        max_bytes = int(cfg.get("log_max_bytes", 1000000))
        backups = int(cfg.get("log_backup_count", 3))
        h = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backups, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        h.setFormatter(fmt)
        logging.getLogger().addHandler(h)
        log.info("File logging → %s (max_bytes=%s backups=%s)", log_file, max_bytes, backups)
    except Exception:
        log.exception("Failed to attach file logging")


async def main():

    # Stub load_config and _metrics_load to avoid NameError
    def load_config():
        return {}

    def _metrics_load(cfg):
        pass

    cfg = load_config()
    _attach_file_logging(cfg)
    _metrics_load(cfg)  # create file if missing
    start_scheduler(cfg)
    await watch_queue(cfg)


# --- Job retention helpers (stubs, module level) ---
def _prune_job_runs(cfg, job_name):
    """Prune old job runs for retention policy (stub)."""
    pass


def _prune_job_zip_archives(cfg, job_name):
    """Prune old job ZIP archives for retention policy (stub)."""
    pass


# --- Stubs for missing functions and imports ---
import os


def get_conn(database_url):
    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def cursor(self):
            return self

        def execute(self, sql):
            pass

    return DummyConn()


try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
except ImportError:

    class AsyncIOScheduler:
        def add_job(self, func, trigger, **kwargs):
            pass

        def start(self):
            pass


# Metrics and notification stubs


def _metrics_bump(cfg, key, success):
    pass


def after_changes_git(cfg):
    pass


def notify_job(cfg, result, success, data, error_msg=None):
    pass


def process_schedule(data, cfg):
    pass


def notify_schedule_error(cfg, name, error):
    pass


# Ensure process_job is defined before usage in async def process_task
# If not, import or define a stub
async def process_job(data, cfg):
    return {}


if __name__ == "__main__":
    asyncio.run(main())
