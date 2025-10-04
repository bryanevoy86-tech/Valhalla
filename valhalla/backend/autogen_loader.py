import importlib.util
import pathlib
import sys

from fastapi import FastAPI

AUTOGEN_DIR = (
    pathlib.Path(__file__).resolve().parents[1] / "heimdall" / "autogen" / "backend" / "routers"
)


def load_autogen_routers(app: FastAPI):
    if not AUTOGEN_DIR.exists():
        return
    for file in AUTOGEN_DIR.rglob("*.py"):
        mod_name = "heimdall_autogen_" + file.stem
        spec = importlib.util.spec_from_file_location(mod_name, file)
        if not spec or not spec.loader:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
        router = getattr(module, "router", None)
        if router:
            app.include_router(router)
