"""Builder orchestration: top-level pipeline that prepares content, runs checks,
and deploys static artifacts.

This is a small scaffold — implement as your pipeline grows.
"""
import pathlib, re
from typing import Dict


def schedule_deploy(payload: Dict) -> Dict:
    """Enqueue and return a status object.

    Replace with queue integration (Redis/RQ/Celery) or direct execution.
    """
    # placeholder: accept payload and return queued
    return {"status": "queued", "payload": payload}

ROUTES_FILE = pathlib.Path("app/main.py")

ROUTE_TEMPLATE_GET = '''
@app.get("{path}")
def {name}():
    return {{"ok": True, "route": "{path}"}}
'''

ROUTE_TEMPLATE_POST = '''
from pydantic import BaseModel
class {model}(BaseModel):
    payload: dict | None = None

@app.post("{path}")
def {name}(body: {model}):
    # TODO: implement
    return {{"ok": True, "received": body.model_dump()}}
'''


def _snake(s: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]+', '_', s).strip('_').lower()


def ensure_route(path: str, method: str = "GET") -> str:
    """Idempotently append a route to `app/main.py`.

    Returns 'exists' if the path is already present or 'created' after appending.
    """
    code = ROUTES_FILE.read_text(encoding="utf-8")
    if path in code:
        return "exists"
    name = _snake(path.strip('/')) or "root"
    if method.upper() == "GET":
        block = ROUTE_TEMPLATE_GET.format(path=path, name=f"{name}_get")
    else:
        block = ROUTE_TEMPLATE_POST.format(path=path, name=f"{name}_post", model=f"{_snake(name)}Model")
    code += "\n" + block + "\n"
    ROUTES_FILE.write_text(code, encoding="utf-8")
    return "created"
