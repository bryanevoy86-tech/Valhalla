from __future__ import annotations
import os, re, pathlib
from typing import Optional

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


def snake(s: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]+', '_', s).strip('_').lower()

def ensure_route(path: str, method: str = "GET") -> str:
    """Idempotently append a route to app/main.py."""
    code = ROUTES_FILE.read_text(encoding="utf-8")
    if path in code:
        return "exists"
    name = snake(path.strip('/')) or "root"
    if method.upper() == "GET":
        block = ROUTE_TEMPLATE_GET.format(path=path, name=f"{name}_get")
    else:
        block = ROUTE_TEMPLATE_POST.format(path=path, name=f"{name}_post", model=f"{snake(name)}Model")
    # append before EOF
    code += "\n" + block + "\n"
    ROUTES_FILE.write_text(code, encoding="utf-8")
    return "created"


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument('path')
    p.add_argument('--method', default='GET')
    args = p.parse_args()
    print(ensure_route(args.path, args.method))
