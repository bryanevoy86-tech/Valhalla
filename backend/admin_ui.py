# --- Recent Events (timeline) ---
def _events_file(_cfg_dict):
    from pathlib import Path as _P

    return _P(ROOT / _cfg_dict.get("events_file", "heimdall/state/events.jsonl"))


def _tail_events(_cfg_dict, limit: int = 50):
    p = _events_file(_cfg_dict)
    rows = []
    if p.exists():
        try:
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
            for ln in lines[-limit:]:
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    pass
        except Exception:
            pass
    rows.reverse()
    return rows


@router.get("/admin/heimdall/api/events")
def api_events(limit: int = 50):
    cfg = _cfg()
    lim = max(1, min(int(limit or 50), 500))
    return {"events": _tail_events(cfg, lim)}


@router.get("/admin/heimdall/ui/timeline")
def ui_timeline(request: Request, limit: int = 200):
    cfg = _cfg()
    ev = _tail_events(cfg, max(1, min(int(limit or 200), 1000)))
    return templates.TemplateResponse("admin/timeline.html", _tpl(request, {"events": ev}))


@router.get("/admin/heimdall/ui/publish")
def ui_publish_now(request: Request):
    return templates.TemplateResponse("admin/publish_now.html", _tpl(request, {}))


@router.get("/admin/heimdall/ui/jobs")
def ui_jobs(request: Request):
    cfg = _cfg()
    jobs_root = ROOT / (cfg.get("jobs", {}).get("jobs_dir", "generated/jobs"))
    items = []
    if jobs_root.exists():
        for name_dir in sorted(jobs_root.iterdir()):
            if not name_dir.is_dir():
                continue
            for run_dir in sorted(name_dir.iterdir(), reverse=True):
                if not run_dir.is_dir():
                    continue
                summary = run_dir / "summary.json"
                if not summary.exists():
                    continue
                try:
                    data = json.loads(summary.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
                items.append(
                    {
                        "name": data.get("name", name_dir.name),
                        "ts": run_dir.name,
                        "return_code": int(data.get("return_code", -1)),
                        "duration_ms": int(data.get("duration_ms", 0)),
                        "cwd": data.get("cwd", ""),
                        "stdout": str((run_dir / "stdout.txt").relative_to(ROOT)),
                        "stderr": str((run_dir / "stderr.txt").relative_to(ROOT)),
                        "summary": str(summary.relative_to(ROOT)),
                        "artifacts": (
                            str((run_dir / "artifacts.json").relative_to(ROOT))
                            if (run_dir / "artifacts.json").exists()
                            else ""
                        ),
                    }
                )
    return templates.TemplateResponse(
        "admin/jobs.html",
        {"request": request, "jobs": items, "now": dt.datetime.now().isoformat(timespec="seconds")},
    )


import datetime as dt
import json
import time
from pathlib import Path
from typing import Dict, List

import yaml
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# validator
from backend.heimdall_validate import lint_task_yaml_str, validate_task

ROOT = Path(__file__).resolve().parent.parent  # repo root
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

router = APIRouter()


@router.get("/admin/heimdall/ui/jobs")
def ui_jobs(request: Request):
    cfg = _cfg()
    jobs_root = ROOT / (cfg.get("jobs", {}).get("jobs_dir", "generated/jobs"))
    items = []
    if jobs_root.exists():
        for name_dir in sorted(jobs_root.iterdir()):
            if not name_dir.is_dir():
                continue
            for run_dir in sorted(name_dir.iterdir(), reverse=True):
                if not run_dir.is_dir():
                    continue
                summary = run_dir / "summary.json"
                if not summary.exists():
                    continue
                try:
                    data = json.loads(summary.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
                items.append(
                    {
                        "name": data.get("name", name_dir.name),
                        "ts": run_dir.name,
                        "return_code": int(data.get("return_code", -1)),
                        "duration_ms": int(data.get("duration_ms", 0)),
                        "cwd": data.get("cwd", ""),
                        "stdout": str((run_dir / "stdout.txt").relative_to(ROOT)),
                        "stderr": str((run_dir / "stderr.txt").relative_to(ROOT)),
                        "summary": str(summary.relative_to(ROOT)),
                        "artifacts": (
                            str((run_dir / "artifacts.json").relative_to(ROOT))
                            if (run_dir / "artifacts.json").exists()
                            else ""
                        ),
                    }
                )
    return templates.TemplateResponse(
        "admin/jobs.html",
        {"request": request, "jobs": items, "now": dt.datetime.now().isoformat(timespec="seconds")},
    )


def _cfg() -> dict:
    cfg_path = ROOT / "heimdall" / "agent.config.json"
    if cfg_path.exists():
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    return {}


def _list_dir(rel: str, pattern: str = "*") -> List[Dict]:
    base = ROOT / rel
    if not base.exists():
        return []
    out = []
    for p in sorted(base.glob(pattern)):
        if p.is_file():
            stat = p.stat()
            out.append(
                {
                    "rel": str(p.relative_to(ROOT)),
                    "size": stat.st_size,
                    "mtime": dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                }
            )
    return out


def _enqueue_task_dict(task: dict) -> Dict[str, str]:
    ok, errs, warns = validate_task(task)
    if not ok:
        return {"queued": "false", "errors": json.dumps(errs), "warnings": json.dumps(warns)}

    cfg = _cfg()
    qdir = ROOT / cfg.get("queue_dir", "heimdall/queue")
    qdir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    ttype = task.get("type", "task")
    fname = qdir / f"{ttype}_{ts}.yaml"
    tmp = qdir / f".{ttype}_{ts}.tmp"
    tmp.write_text(yaml.safe_dump(task, sort_keys=False), encoding="utf-8")
    tmp.replace(fname)
    return {"queued": "true", "file": str(fname.relative_to(ROOT)), "warnings": json.dumps(warns)}


@router.get("/admin/heimdall/ui")
def ui_home(request: Request):
    cfg = _cfg()
    metrics_path = ROOT / cfg.get("metrics_file", "heimdall/state/metrics.json")
    metrics = {"note": "metrics not created yet"}
    if metrics_path.exists():
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception as e:
            metrics = {"error": f"failed to read metrics: {e}"}

    counts = {
        "queue": len(
            [
                f
                for f in _list_dir("heimdall/queue", "*.yaml")
                if not f["rel"].endswith(".done.yaml") and not f["rel"].endswith(".error.yaml")
            ]
        ),
        "errors": len(_list_dir("heimdall/queue", "*.error.yaml")),
        "previews": len(_list_dir("generated", "*")),
    }
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "metrics": metrics,
            "counts": counts,
            "now": dt.datetime.now().isoformat(timespec="seconds"),
        },
    )


@router.get("/admin/heimdall/ui/queue")
def ui_queue(request: Request):
    files = [
        f
        for f in _list_dir("heimdall/queue", "*.yaml")
        if not f["rel"].endswith(".done.yaml") and not f["rel"].endswith(".error.yaml")
    ]
    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "title": "Queue",
            "files": files,
            "now": dt.datetime.now().isoformat(timespec="seconds"),
        },
    )


@router.get("/admin/heimdall/ui/errors")
def ui_errors(request: Request):
    files = _list_dir("heimdall/queue", "*.error.yaml")
    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "title": "Errors",
            "files": files,
            "now": dt.datetime.now().isoformat(timespec="seconds"),
        },
    )


@router.get("/admin/heimdall/ui/previews")
def ui_previews(request: Request):
    files = _list_dir("generated", "*")
    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "title": "Previews",
            "files": files,
            "now": dt.datetime.now().isoformat(timespec="seconds"),
        },
    )


@router.get("/admin/heimdall/ui/logs")
def ui_logs(request: Request, lines: int = 400):
    cfg = _cfg()
    log_file = ROOT / cfg.get("log_file", "heimdall_action.log")
    content = ""
    if log_file.exists():
        txt = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        content = "\n".join(txt[-max(10, min(lines, 5000)) :])
    return templates.TemplateResponse(
        "admin/logs.html",
        {
            "request": request,
            "content": content,
            "lines": lines,
            "log_file": str(log_file.relative_to(ROOT)),
            "now": dt.datetime.now().isoformat(timespec="seconds"),
        },
    )


@router.get("/admin/heimdall/ui/raw")
def ui_raw(rel: str):
    if rel.startswith("/") or ".." in rel:
        raise HTTPException(400, "invalid path")
    p = ROOT / rel
    if not p.exists() or not p.is_file():
        raise HTTPException(404, "not found")
    data = p.read_text(encoding="utf-8", errors="ignore")
    return PlainTextResponse(data, media_type="text/plain; charset=utf-8")


@router.get("/admin/heimdall/ui/compose")
def ui_compose(request: Request):
    return templates.TemplateResponse(
        "admin/compose.html",
        {"request": request, "now": dt.datetime.now().isoformat(timespec="seconds")},
    )


@router.post("/admin/heimdall/ui/compose")
def ui_compose_post(request: Request, yaml_text: str = Form(...)):
    lint = lint_task_yaml_str(yaml_text)
    if not lint.get("ok"):
        # show page again with lint output; the client-side script will also handle lint, but we guard here too
        return templates.TemplateResponse(
            "admin/compose.html",
            {"request": request, "now": dt.datetime.now().isoformat(timespec="seconds")},
        )
    task = lint.get("normalized") or {}
    res = _enqueue_task_dict(task)
    # After enqueue, bounce to Queue for clarity
    return RedirectResponse(url="/admin/heimdall/ui/queue", status_code=303)


@router.get("/admin/heimdall/ui/compose2")
def ui_compose_v2(request: Request):
    return templates.TemplateResponse("admin/compose_v2.html", _tpl(request, {}))


@router.get("/admin/heimdall/ui/knowledge")
def ui_knowledge(request: Request):
    return templates.TemplateResponse("admin/knowledge.html", _tpl(request, {}))
