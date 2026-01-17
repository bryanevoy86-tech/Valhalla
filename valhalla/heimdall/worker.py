#!/usr/bin/env python3
"""
Heimdall Python Worker — watches heimdall/queue for *.yaml, renders Jinja2 templates
from heimdall/templates, writes outputs, and moves processed tasks.
"""
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

ROOT = Path.cwd()
CFG_FILE = ROOT / "heimdall" / "agent.config.json"


def load_cfg() -> Dict[str, Any]:
    default = {
        "queue_dir": "heimdall/queue",
        "templates_dir": "heimdall/templates",
        "background_build": True,
        "max_parallel_jobs": 2,
    }
    if CFG_FILE.exists():
        try:
            default.update(json.loads(CFG_FILE.read_text()))
        except Exception:
            pass
    return default


CFG = load_cfg()
QUEUE_DIR = ROOT / CFG["queue_dir"]
TPL_DIR = ROOT / CFG["templates_dir"]
PROCESSED_DIR = QUEUE_DIR / "processed"
ERROR_DIR = QUEUE_DIR / "error"

env = Environment(
    loader=FileSystemLoader(str(TPL_DIR)),
    autoescape=False,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)


def log(*a):
    print("[Heimdall-Worker]", *a, flush=True)


def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def run_post(steps: List[str]):
    if not steps:
        return
    for s in steps:
        s = s.strip()
        if s.startswith("touch "):
            rel = s.replace("touch ", "").strip()
            dest = ROOT / rel
            ensure_parent(dest)
            with open(dest, "a", encoding="utf-8") as f:
                f.write(f"{int(time.time())}\n")
            log("Touched", rel)
        else:
            log("Skipped unsupported post step:", s)


def handle_task_obj(obj: Dict[str, Any]):
    if "template" not in obj or "output" not in obj:
        raise ValueError("Task missing 'template' or 'output'")
    template_rel = obj["template"]
    output_rel = obj["output"]
    context = obj.get("context", {})

    tpl = env.get_template(template_rel)
    rendered = tpl.render(**context)

    out_path = ROOT / output_rel
    ensure_parent(out_path)
    out_path.write_text(rendered, encoding="utf-8")
    run_post(obj.get("post"))
    log("Rendered:", template_rel, "→", output_rel)


def process_yaml(file: Path):
    log("Processing:", file.name)
    try:
        data = yaml.safe_load(file.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "tasks" in data and isinstance(data["tasks"], list):
            for t in data["tasks"]:
                handle_task_obj(t)
        else:
            handle_task_obj(data)

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file), str(PROCESSED_DIR / file.name))
        log("Done:", file.name)
    except Exception as e:
        ERROR_DIR.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(file), str(ERROR_DIR / file.name))
        except Exception:
            pass
        log("ERROR:", file.name, "-", str(e))


def scan_once():
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    for f in QUEUE_DIR.glob("*.y*ml"):
        process_yaml(f)


class QueueHandler(FileSystemEventHandler):
    def on_created(self, event):
        p = Path(event.src_path)
        if p.suffix in (".yaml", ".yml"):
            time.sleep(0.15)
            process_yaml(p)

    def on_modified(self, event):
        p = Path(event.src_path)
        if p.suffix in (".yaml", ".yml"):
            time.sleep(0.15)
            process_yaml(p)


def run_watch():
    scan_once()
    observer = Observer()
    observer.schedule(QueueHandler(), str(QUEUE_DIR), recursive=False)
    observer.start()
    log("Watching", str(QUEUE_DIR.relative_to(ROOT)), "… (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    if "--once" in sys.argv:
        scan_once()
    else:
        run_watch()
