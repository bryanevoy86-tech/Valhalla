import shutil
import time
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path.cwd()
QUEUE_DIR = ROOT / "heimdall" / "queue"
TPL_DIR = ROOT / "heimdall" / "templates"
PROCESSED_DIR = QUEUE_DIR / "processed"
ERROR_DIR = QUEUE_DIR / "error"

env = Environment(loader=FileSystemLoader(str(TPL_DIR)), autoescape=False)


def log(*a):
    print("[Heimdall]", *a, flush=True)


def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def handle_task(data):
    template = data["template"]
    output = data["output"]
    context = data.get("context", {})
    tpl = env.get_template(template)
    rendered = tpl.render(**context)
    out_path = ROOT / output
    ensure_parent(out_path)
    out_path.write_text(rendered, encoding="utf-8")
    log("Rendered:", template, "→", output)


def process_yaml(file: Path):
    log("Processing:", file.name)
    try:
        data = yaml.safe_load(file.read_text())
        if "tasks" in data:
            for t in data["tasks"]:
                handle_task(t)
        else:
            handle_task(data)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file), str(PROCESSED_DIR / file.name))
        log("Done:", file.name)
    except Exception as e:
        ERROR_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file), str(ERROR_DIR / file.name))
        log("ERROR:", file.name, "-", e)


def main():
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    log("Watching", QUEUE_DIR)
    while True:
        for f in list(QUEUE_DIR.glob("*.yaml")) + list(QUEUE_DIR.glob("*.yml")):
            process_yaml(f)
        time.sleep(2)


if __name__ == "__main__":
    main()
